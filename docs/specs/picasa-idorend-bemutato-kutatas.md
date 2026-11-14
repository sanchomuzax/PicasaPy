# A Picasa Időrend-bemutatójának bináris kutatása, 2. rész (#5401)

A 38.2.1-38.2.60 szakasz a [picasa-idorend-viselkedes.md](picasa-idorend-viselkedes.md) lapon van; ez a lap a 38.2.61-től folytatja a számozást, mert az első lap elérte az 1 MB-os fájlméret-korlátot (#5599).

#### 38.2.61 A Ghidra-kimenet ellenőrzése és a kártyagörbe QEMU-mérése (#5401, 2026-10-22)

**Hatókör.** A `referencia/ghidra/2026-10-22-ghidra-sor-197-200.txt` `0x005e81e0` kimenetének ellenőrzése, valamint a qshow-kártyagörbe (`0x007fbab0`) számszerű futtatásos kontrollja. A mérő-archívumban nincs `timeline`, `idorend`, `qshow`, `job-102` vagy `job-217` tag; ebből nem következik, hogy ilyen mérés sehol nincs. A próba a `copy_Picasa_3_7` könyvtárban levő `runtime/bezier.txt` fájlt és a `Picasa3.exe` függvényét használta. Az exe verzióját az akkori bejegyzés nem rögzítette; a fájl tényleges PE-verzióját a 38.2.85 azonosítja. A `bezier.txt` fájl saját verziója **NINCS MEG**. Az ideiglenes ELF a munkafa `.bt/` könyvtárában készült, majd a mérés után törölve lett. Terméki kód nem változott.

**1. A `0x005e81e0` nem az Időrend animátora - megerősített.**

- **A út - utasításszintű olvasás.** A függvény 802 bájt. A `0x005e82e2`-`0x005e82e7` a `0xc811d4` (`"]star"`) kulccsal hívja a `0x00475250`-et; a `0x005e83d8`-`0x005e83e9` a `stars/yes` (`0xc97860`) vagy `stars/no` (`0xc9786c`) erőforrást választja, majd a `0x00410fa0`-nak adja. A célfüggvény diszasszemblálása ezeket a címeket és ágakat közvetlenül igazolja.
- **B út - független Ghidra-kimenet és hívóellenőrzés.** A friss Ghidra-kimenet három közvetlen hívót sorol fel: `0x005d9cc0`, `0x005e60d0`, `0x00760240`. Az index `xrefs` táblája ugyanezt a hívófüggvény-készletet adja; a hívóhelyeket külön diszasszemblálás ellenőrizte: `0x005db0c5` a `thumbui/startoggle` ágban, `0x005e6587` a billentyűkezelő `push 2` ágában, `0x007606fd` pedig az `editoneup/star` ágban van. A Ghidra-kimenet és az utasításolvasat tehát egyezik: ez a függvény csillagállapotot kezel és csillagjelzőt készít.
- **Cáfoló kísérlet.** Megpróbáltam cáfolni azt a besorolást, hogy a `0x005e81e0` csillagjelző-függvény, és helyette az Időrend animátorának tekinteni. A közvetlen hívók három csillag-műveleti ág; a függvény saját kulcsa `]star`, a kirajzolt erőforrása `stars/yes` vagy `stars/no`. A cáfolat nem állt meg. Ez kizárja, hogy a `0x005e81e0` maga legyen a kártya-animátor vagy kártyaforrás; az Időrend magasabb szintű útjából való minden közvetett kapcsolatot nem minősíti.
- **Bizonyítottsági fok: megerősített** erre az egy besorolásra, mert a Ghidra dekompilációja és a független utasításszintű út/hívóellenőrzés egybeesik. A kimenet nem ad új választ az Időrend négy teljes kutatási pontjára.

**2. A `0x007fbab0` racionális köbös Bézier-görbéje - megerősített az itt mért bemenettel.**

Az `0x007fbd90` négy `"%f %f %f\n"` rekordot olvas a `runtime\bezier.txt` fájlból a `P+0x50..0x7c` mezőkbe (38.2.25 §2). A `copy_Picasa_3_7` könyvtárban levő fájl első négy, aktív rekordja; az ezt követő `#` sorok nem kerülnek beolvasásra:

| pont | x | y | súly | forrás |
|---|---:|---:|---:|---|
| P0 | -3 | -3 | 10 | mérés (a helyi `runtime/bezier.txt` pontos tartalma) |
| P1 | -1 | -0.5 | 4 | mérés (a helyi `runtime/bezier.txt` pontos tartalma) |
| P2 | -0.3 | 0.9 | 0.6 | mérés (a helyi `runtime/bezier.txt` pontos tartalma) |
| P3 | 0.9 | 0.75 | 1.1 | mérés (a helyi `runtime/bezier.txt` pontos tartalma) |

**A út - bináris.** A `0x007fbab0` diszasszemblye a négy pont x/y mezőiből Bernstein-számlálókat, a súlymezőkből nevezőt képez; a végső osztás és középre tolás az `0x007fbc6f`-`0x007fbcaf` tartományban történik. Képlete a 38.2.38 §3 szerint: `b0=(1-t)^3`, `b1=3(1-t)^2t`, `b2=3(1-t)t^2`, `b3=t^3`; `D=Σ bi·wi`; `x=(Σbi·xi-0.5)/D+0.5`, `y=(Σbi·yi-0.5)/D+0.5`, `z=1/D`. A kód a számlálóban nem szorozza az x/y koordinátákat a súlyokkal.

**B út - QEMU-futtatás az eredeti gépi kódon.** A `qemu-i386` alatt a `0x007fbab0` függvényt hívtam meg a fenti négy ponttal és `t` f32 bemenetekkel. A három f32 kimenet egyezik a képlet külön kiszámított eredményével az f32 kerekítés pontosságáig:

| t bemenet | kimenet (x, y, z; QEMU f32) | nyers kimeneti bájtok | forrás |
|---:|---|---|---|
| 0 | (0.150000006, 0.150000006, 0.100000001) | `9a99193e 9a99193e cdcccc3d` | mérés (`qemu-i386`, `0x007fbab0`) |
| 0.5 | (0.0983935595, 0.297188729, 0.321285158) | `9082c93d 1f29983e 7d7fa43e` | mérés (`qemu-i386`, `0x007fbab0`) |
| 1 | (0.863636315, 0.727272749, 0.909090877) | `45175d3f 8c2e3a3f 2eba683f` | mérés (`qemu-i386`, `0x007fbab0`) |

**Cáfoló kísérlet.** A szokásos racionális Bézier-alakból kiinduló, súlyozott `Σbi·wi·xi` / `Σbi·wi` számlálót ellenőriztem a `t=0.5` mintán. Az így kapott x/y nem egyezik a natív függvény QEMU-kimenetével; a súlyozatlan `Σbi·xi` / `Σbi·yi` számláló egyezik. Ez a cáfoló is teljesítette ugyanazt a mércét: a bemenet ugyanaz a négy pontos fájlsor, a döntő kimenet a bináris függvényé.

**Bizonyítottsági fok: megerősített** a `0x007fbab0` képletére és a táblázatban szereplő helyi vezérlőpontokra. Ez nem zárja le a teljes Időrend-mozgást: a kártyák forrása és sorrendje, a képkockánkénti helyzet/átlátszóság összekötése, a teljes időzítési görbe, a rétegsorrend és a háttér viselkedése továbbra is külön kérdés.

**Hatás a #5401 „Kész, ha” pontjaira:** (1) forráshalmaz és sorrend - nincs új lezárás; (2) mozgás - a kártyagörbe képlete és a helyi vezérlőpontok számszerű QEMU-kontrollja megvan, a teljes animáció nem; (3) vezérlők - ez a kör nem zárta a `timelinedot`, dátumcsúszka, automatikus léptetés és billentyűk teljes működését; (4) diavetítésbe lépés és visszatérés - ez a kör nem zárta le.

#### 38.2.62 Az Időrend véletlen eltolásának helyesbítése és a képkocka-transzformáció QEMU-mérése (#5401, 2026-10-22)

**Hatókör és módszer.** A `0x00802230` véletlen eltolásának és előzőérték-másolásának, továbbá a `0x007fff30` képkocka-transzformációjának és alfa-kimenetének vizsgálata. Az utasításokat a helyi `Picasa3.exe`-ből olvastam; a struktúratag-találatokat a teljes `.text`-en a kötelező `paszta.memoria_kapu()` után futó `paszta.py`-pásztázás adta. Mindkét függvényt az eredeti gépi kódon futtattam `qemu-i386` alatt. A próbák kézzel felépített `this`-állapotot és vezérelt `rand()`-visszatérést használtak; a nem célzott segédfüggvényekhez a QEMU-harness stubbokat adott. Ez nem qshow-felvétel, és nem igazolja a normál futás teljes objektumforrását. Az ideiglenes fájlok a munkafa `.bt/` könyvtárában készültek.

##### §1 A `0x00802230` véletlen eltolása pozitív

**A út - bináris utasítások.** A függvény két `rand()`-hívása `0x008022db` és `0x008022f2`; a második visszatérését a `0x008022f7`-`0x008022ff`, az elsőét a `0x008022e0`-`0x008022eb` bitművelete alakítja float-bitté. Az `(r + 0x3f8000) << 8` eredménye `0x3f800000 + r·256`, amely floatként `1 + r/32768`, pontosan ábrázolható. A `0x00802306`-tól az x-ág ezt 1-ből kivonja; a `0x00802353`-tól a y-ág ugyanezt teszi. A méretelőjel-korrekció az x-ágban `0x00802332`-`0x0080233b`, a y-ágban `0x00802376`-`0x0080237f`; az új `[this+0x400]`/`[this+0x404]` mezőbe írás a `0x00802391`/`0x008023a1` címeken történik. Az előző értékek másolása `0x008022c3`-`0x008022d5`.

Legyen `c = 0,1499999761581421` (f64, `0x00cf4320`), `W = [this+0x474]`, `H = [this+0x478]`, és `W'`, illetve `H'` az adott 32 bites méret, negatív előjelnél `2^32` hozzáadásával (`0x00cf39e4`, `0x00cf3ac0`). `r1` az első, `r2` a második `rand()`-érték:

- `x = fl32(c · W' · r2 / 32768)`;
- `y = fl32(c · 0,5 · H' · r1 / 32768)` (`0,5`: f64 `0x00c72150`).

Nemnegatív méretek és 0…32767 közötti `rand()`-érték mellett `0 ≤ x < c·W` és `0 ≤ y < 0,5·c·H`. A `0,5` és `c` szorzó, a méretelőjel-korrekció és a tárolási címek közvetlenül a bináris utasításaiból olvashatók. Hogy W és H képméret vagy kártyaméret, ebből nem következik.

**B út - QEMU az eredeti `0x00802230` gépi kódján.** `W=640`, `H=480`, előző eltolás `(0,25; -0,125)` mellett a `rand()`-ot a felsorolt értékekre vezéreltem. A függvény két hívást végzett; az új mezők és az elmentett előző értékek:

| `r1` (y), `r2` (x) | új `(x,y)` a binárisban | előző érték utána | forrás |
|---:|---:|---:|---|
| 0, 0 | (0; 0) | (0,25; -0,125) | mérés (`qemu-i386`, `0x00802230`) |
| 32767, 32767 | (95,9970550537; 35,9988975525) | (0,25; -0,125) | mérés (`qemu-i386`, `0x00802230`) |
| 16384, 32767 | (95,9970550537; 17,9999961853) | (0,25; -0,125) | mérés (`qemu-i386`, `0x00802230`) |

**A két út és a cáfoló próba.** Az utasításszintű bitminta-levezetés pozitív `r/32768` szorzót ad; ettől függetlenül a QEMU az eredeti függvényben, rögzített bemenetekkel pozitív `(95,9970550537; 35,9988975525)` eltolást mért a maximális `rand()`-értéknél. A régi `u-1` képlet ezt negatív előjelűnek jósolná, ezért a próba megcáfolja a 38.2.34 korábbi előjelét. A QEMU a célfüggvény eredeti bájtjait futtatta; a `rand()` bemenetet és a méretmezőket rögzítettem, majd a visszatérő mezőket olvastam ki. A próba nem általánosítható a teljes qshow-futásra vagy a véletlen seedre.

##### §2 A `0x007fff30` transzformációi és alfája

**A út - bináris utasítások és mezőpásztázás.** A teljes `.text`-pásztázás a `0x00802230` írásait mutatja: a jelenlegi eltolás a `[this+0x400]`/`[this+0x404]`, az előző a `[this+0x408]`/`[this+0x40c]` mező. A `0x007fff30` közvetlenül mind a négyet olvassa (`0x007fffeb`, `0x007fffff`, `0x00800023`, `0x00800038`). A konstansok a `0x00cf4848` (f64 `1,1`), `0x00cf4850` (f64 `0,17647055523618382`), `0x00cf39f8` (`3`), `0x00c7d9d0` (`2`) és `0x00c72150` (`0,5`) címeken vannak. A `0x00800095` és `0x008000d7` tíz dword-ot másol a transzformációs rekordokba (`this+0x4e4`, illetve `this+0x4bc`); a további mezőírások a léptéket és eltolást tárolják. A `this+0x3f4 == 0` ágon (`0x0080015d`-`0x00800199`) a `this+0x4bc` rekord identitásmátrixra áll.

`0 ≤ t ≤ 1` esetén, a normál `SimpleSlideshow == 0` rajzolási ágban, az utasítássor a következő leképezéseket valósítja meg (az x87-köztes műveletek és a f32 mezőírás kerekítése a bináris számítás része):

- `g(v) = 1 / (1,1 + 0,17647055523618382 · v³ / 8)`;
- `p_c(t) = t² · (3 - t) / 4`, `p_p(t) = 1 - ((1 - t)² · (1 + t/2)) / 2`;
- `this+0x4e4` (jelenlegi eltolás): skála `g(t)`, `tx = 1 + p_c(t)·[this+0x400]`, `ty = 1 + p_c(t)·[this+0x404]`;
- `this+0x4bc` (előző eltolás): skála `g(t+1)`, `tx = 1 + p_p(t)·[this+0x408]`, `ty = 1 + p_p(t)·[this+0x40c]`; ha `[this+0x3f4] == 0`, ezt a rekordot a függvény identitásra cseréli.

Mindkét rekord 2D, tengelypárhuzamos affin mátrix: a két átlóelem azonos skála, a forgatási/keresztirányú elemek 0, a homogén jobb alsó elem 1. Ez a helper kimenete; a tömbök képforrása és a két transzformáció vásznon látható szerepe ettől még nincs azonosítva.

**A két bemenet kapcsolása (`0x008001c0` → `0x00aa6180`, diszasszembly).** A hívó a `this+0x444` és `this+0x4bc` párt, majd a `this+0x46c` és `this+0x4e4` párt adja át (`0x008001c0`, 38.2.30 §1). A `0x00aa6180` első párját a `0x00aa5fb0`-nak adja; ha az alfa nem nulla, ugyanígy előállítja a második párt is, majd a két köztes képpufferrel és az alfával a `0x009dc040`-et hívja (`0x00aa61fd`-`0x00aa6245`). Alfa nulla esetén a második pár és ez a kétpufferes ág kimarad. Ezzel a descriptor-transzformáció párosítás és az alfa szerinti kétbemenetű út megvan; hogy a descriptorok milyen képeket tartalmaznak és a vásznon melyik rétegként jelennek meg, **NINCS MEG**.

Az alfa-kimeneti mutatót a `0x00800057` nullázza. A `0x00800110`-`0x00800153` a `0xcf4840` f32 küszöböt (`0,6800000071525574`) vizsgálja, majd a `0xcf39d8` f64 `256`-tal szoroz, a `0xcf4830` f64 `0,3199999928474426`-tal oszt, és a `0xc00` kerekítési módot állítja a `fistp` művelethez. A helper kimenete: ha `t > 0,6800000071525574`, `trunc_toward_zero(256·(t-0,6800000071525574)/0,3199999928474426)`, különben 0. A helper nem vágja 256-ra az értéket; a `0x008001c0` egyszerű ágában a hívó `t` értéke legfeljebb 1 (`SimpleSlideshow == 0`, 38.2.30 §1).

**B út - QEMU az eredeti `0x007fff30` gépi kódján.** A kézzel beállított `this`-állapotban a jelenlegi eltolás `(0,25; -0,125)`, az előző `(-0,5; 0,25)` volt. A táblázat a kimeneti rekordok `(skála; tx; ty)` mezőit adja. Az `index=0` az identitáságat aktiválja az előző rekordhoz; `index=1` meghagyja az előző eltolás transzformációját.

| `t` | index | `this+0x4bc` előző rekord | `this+0x4e4` jelenlegi rekord | alfa | forrás |
|---:|---:|---|---|---:|---|
| 0 | 0 | (1; 0; 0) | (0,909090877; 1; 1) | 0 | mérés (`qemu-i386`, `0x007fff30`) |
| 0 | 1 | (0,891218841; 0,75; 1,125) | (0,909090877; 1; 1) | 0 | mérés (`qemu-i386`, `0x007fff30`) |
| 0,5 | 0 | (1; 0; 0) | (0,906817794; 1,0390625; 0,98046875) | 0 | mérés (`qemu-i386`, `0x007fff30`) |
| 0,5 | 1 | (0,851463497; 0,578125; 1,2109375) | (0,906817794; 1,0390625; 0,98046875) | 0 | mérés (`qemu-i386`, `0x007fff30`) |
| 0,75 | 1 | (0,820868850; 0,521484375; 1,23925781) | (0,901464462; 1,07910156; 0,960449219) | 55 | mérés (`qemu-i386`, `0x007fff30`) |
| 1 | 1 | (0,783410192; 0,5; 1,25) | (0,891218841; 1,125; 0,9375) | 256 | mérés (`qemu-i386`, `0x007fff30`) |
| 1,1 | 1 | - | - | 336 | mérés (`qemu-i386`, `0x007fff30`) |

Az alfa-határ körüli további QEMU-próbák: `t=0,6799999475`, `0,6800000072` és `0,6800000668` mind 0-t adott; `t=0,68359375` 2-t, `0,9999999404` 255-öt. Az 1,1-es bemenet nem normál hívóoldali tartomány, csak azt mutatja, hogy a helper maga nem korlátozza az alfát.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a `+0x4bc` rekord az előző, a `+0x4e4` pedig a jelenlegi eltolást használja. `t=0,5`-nél külön-külön nulláztam az előző és a jelenlegi eltolást: az előző nulla kizárólag a `+0x4bc` transzlációját vitte `(1,1)`-re, a jelenlegi nulla kizárólag a `+0x4e4` transzlációját. A próba nem cáfolta a mező-hozzárendelést. Az eredeti bináris függvény azonos bemeneti állapota mellett csak az egyik eltolást változtattam, majd a kimeneti rekordokat olvastam ki.

**Bizonyítottsági fok és határ.** A `0x00802230` eltolásképlete és előzőérték-másolása, továbbá a `0x007fff30` két transzformációjának mező-hozzárendelése és alfa-leképezése itt **megerősített**: az utasításszintű út és az eredeti gépi kód vezérelt QEMU-kimenete egyezik; a régi negatív előjel ellen külön cáfoló próba futott. Ez nem azonosítja a képlánc forrását és sorrendjét, a két transzformáció képforrását/vizuális sorrendjét, a kártya- és háttérrajzolást, az összes `SimpleSlideshow` ágat, a csúszkát vagy a diavetítésből visszatérő állapotot. A #5401 teljes státusza továbbra is **nyitott**.

**A #5401 „Kész, ha” pontjai.** (1) Képlánc, forráshalmaz, rendezés és gyűjteményenkénti elemszám: ⛔ a lista mezői megvannak, a provider/kollekció és sorrend nem (`0x004039f0`, `0x008018a0`). (2) Átmenet pálya, képméret, forgatás, alfa, időzítés és háttér/kártyarajz: ⛔ a véletlen eltolás, a helper két affin kimenete és a helper alfa-képlete megerősített, de a képforrások, vizuális összekötés, teljes időgörbe és rajzolási rétegek nyitottak; qshow-képkocka-felvétel nem készült. (3) Vezérlők, dátumcsúszka, automatikus lépés, szóköz és nyilak: ⛔ a teljes működés továbbra sincs meg. (4) Diavetítésbe lépés és a pontos visszatérési kép/gyűjtemény: ⛔ nyitott.

**Nyitott.**

- A fenti kérdésekhez a Ghidra-kimenet már elérhető a 2026-10-22-i 202-209 sorban: `0x004039f0`, `0x008018a0`, `0x00aa6180`, `0x00aa5fb0`, `0x00a52890`, `0x005e60d0` és `0x008032e0`. A `+0x2bc` szolgáltató `CThumbDB`, a qshow token→`CSlice` út és a billentyűkezelő külön `0x00801270` címe tisztázott. Nyitott maradt a `CThumbUI+0x2c0` forráskollekció, a `+0x50c` indexelt token konkrét neve/típusa és a fotók; a keverő (blend) hívások bemeneti rétegei; az overlayek teljes eseményútja; valamint a `Home/End` és a hostból visszatérés felhasználói hatása. Ezeket a meglévő dekompilálások hívóinak, vtable-bejegyzéseinek és a célzott futásmérésnek az összevetésével kell megszerezni, nem ugyanazon címek újra-dekompilálásával.
- A Space/Auto Play statikus, állapotfüggő módváltási útját a 38.2.64 és a 38.2.65 bontja ki; a futásidejű előfeltétel és a visszatérő gyűjtemény/képpozíció mérésként nyitott.
- A `0x008032e0` Ghidra-kimenete megvan; a qshow `ytWindow` host célja `0x00983270`-ként azonosított. A ténylegesen visszaállított gyűjteményt és képindexet futás előtti/utáni mérés tudja eldönteni; ez **NINCS MEG**.

**Új kutatási jegyjavaslat.** Nincs; a nyitva maradt kérdések a #5401 elfogadási pontjaihoz tartoznak, nem külön feladatok.

#### 38.2.63 A qshow billentyűútja, a listaépítés és a csúszka indexleképezése (#5401, 2026-10-22)

**Hatókör és módszer.** A nyolc, a 38.2.62 végén felsorolt cím Ghidra-kimenete elkészült (belső Ghidra-referencia, 2026-10-22, sor 202-209). A döntő ágakat külön, függvényenkénti `annot_disasm.py` diszasszemblálás ellenőrizte az eredeti `Picasa3.exe`-ből. A `CThumbUI+0x2c0` és a qshow `+0x388` mező közvetlen íróit célzott, darabolt `paszta.py` `.text`-pásztázás kereste; a `paszta.memoria_kapu()` a pásztázás előtt lefutott. A mérőadat-archívumban nem volt Időrend/qshow-felvételhez tartozó tag, ezért ebben a körben futás közbeni képkockafelvétel és QEMU-mérés nem készült. A régi Ghidra-kéréslista aktuális állapota: a célfüggvények dekompilálása elkészült; a maradék kérdések e szakasz Nyitott listájában vannak.

##### §1 A képlánc bemenetének egy része és a sorrend

**A út - utasítások és adatfolyam.** A `0x004039f0` `0x3710` bájtos `CThumbUI`-objektumot foglal, majd a `0x005643e0` konstruktornak a hívó `[X+0x1030]` és `[X+0x1038]` mezőjét adja át (`0x00403d9e`-`0x00403db8`; Ghidra-kimenet: `2026-10-22-ghidra-sor-202-209.txt`, `0x004039f0`). A konstruktor a `[this]` mezőbe a `0x00c9052c` `CThumbUI::vftable`-t, továbbá a `+0x2bc`, `+0x2c0` és `+0x2c4` mezőbe kapott értékeket írja (`0x00564507`, `0x005644fa`, `0x00564616`, `0x0056461c`). A külön `[X+0x1034]` mezőt a `0x00402f90` a `0x00415790` eredményével tölti (`0x00402fd3`-`0x00402fdc`); ez nem a `0x004039f0` konstruktorának átadott két mező egyike.

**B út - független RTTI/vtable-ellenőrzés.** Az index `rtti` táblája a `0x00c9052c` címet `CThumbUI::vftable`-ként, a `0x00c81f78` címet `CThumbDB::vftable`-ként azonosítja. Ettől független gépikód-út, hogy a `0x00415790` konstruktor a `[this]` mezőbe a `0x00c81f78` vtable-címet írja (`0x004157fd`), a `0x00562cc0` thunk pedig a `CThumbUI+0x2bc` objektum vtable `+0x20` helyére továbbít. Ezek együtt azonosítják a `+0x2bc` szolgáltató osztályát `CThumbDB`-ként; ez az objektum nem azonos a qshow `+0x2c0` bemeneti mezőjével.

A qshow bemeneti lánca külön követhető. A `0x005e8a70` a `0x005e96d9` címen a `CThumbUI+0x2c0` értékét az átadott paraméterrekord `+0x14` mezőjébe írja; a `0x008037e0` ezt a rekordot továbbadja a `0x007fa7f0` oneup-konstruktornak, amely a paraméter `+0x14` mezőjét a saját `+0x2f4` mezőjébe másolja (`0x007fa83b`-`0x007fa83e`). A `0x008018a0` ezt a `[this+0x2f4]` bemenetet adja át a `0x004b0190`-nek. **Független út:** a `0x005e9434` ugyanezt a `CThumbUI+0x2c0` mezőt adja át a `0x004a0980` elemszám-kérőnek; a `0x005e9490` indexhurok ezután a `CThumbUI` vtable `+0x90` metódusát hívja, a `0x00562cc0` thunk pedig a külön `CThumbUI+0x2bc` `CThumbDB` objektum vtable `+0x20` helyére továbbít. Az első, közvetlen descriptor-átadási lánc egy útból ismert (**feltételes**); a második, ettől külön count/index út megerősíti, hogy a `+0x2c0` mezőt ugyanebben a MakeTimeline ágban is használják. Ez nem bizonyítja, hogy a count/index hurok kimenete azonos a qshow descriptor-listájával. A `+0x2c0` mögötti kollekció típusa, album-/mappa-tagsága és elemlistája nincs meg.

**Pontosítás a 38.2.6/38.2.8 korábbi olvasatához.** A `0x005e96eb` külön a `[CThumbUI+0xeac]` értékét tölti a hívó paraméterrekord `+4` mezőjébe (`0x005e96fc`-`0x005e9709`). A oneup-konstruktor ezt a másik argumentumot a `0x007fb9f0`-nek adja át, amely a `[oneup+0x2f8]+4`, vagyis `oneup+0x2fc` mezőbe másolja (`0x007fa844`-`0x007fa850`, `0x007fb9f3`). Ez külön adat a közvetlen descriptor-bemenettől (`CThumbUI+0x2c0` → `oneup+0x2f4`); önmagában nem bizonyítja, hogy szűrő, és a régi `[this+0xeac]` köztes lista qshow-descriptorral való kapcsolata nincs meg.

A `0x008018a0` a `0x004b0190` által kapott `CSlice` posting-list elemszámát `[slice+0x64]+4`, majd `>> 1` alakban olvassa, és a 0-tól növelt indexével járja be (`0x00801952`-`0x00801bd5`). A hurok a `CSlice+0x64` listaelemeit a `[qshow+0x3ec]` tömbbe fűzi, a kizárási jelző alapján elemeket kihagyva; a fennmaradó elemek sorrendjét nem rendezi át. A szolgáltató, a vtable-hely és a `CSlice`-t kitöltő függvény az alábbi, 2026-10-23-i kiegészítésben azonosított. A `+0x50c` index forrásmechanizmusa ismert, de az indexelt token konkrét neve/típusa, a képi rekordok feloldása és a gyűjteményenkénti képszám továbbra sincs meg.

##### §1/a A qshow token→`CSlice` lekérdezése (2026-10-23)

**A út - qshow hívási lánc és eredeti utasítások.** A `0x008018a0` az EAX-ben kapott indexet a qshow `[this+0x50c]` mezőjébe írja (`0x008018b2`-`0x008018b8`), majd az indexet veremargumentumként és a `[this+0x2f4]` állapotobjektumot EAX-ben a `0x004b0190`-nek adja (`0x008018c7`-`0x008018e0`). Mindhárom ismert hívó indexforrása követhető. A qshow indulásakor a `0x008037e0` EAX=0-val hívja a rutint (`0x0080394f`-`0x00803953`). Az időzítetten ismétlődő `0x00801cb0` a qshow `+0x2f8` adatobjektumával meghívja a `0x007fd8c0`-t, kimeneti címként `qshow+0x510`-et ad, majd sikeres találatkor az ott kapott dwordot tölti EAX-be és hívja a `0x008018a0`-t (`0x00801ccf`-`0x00801ce5`). A `0x007fd8c0` a kiválasztott `0xf8` bájtos rekord első dwordját írja a kimenetbe (`0x007fd965`-`0x007fd97a`). Az egér-találati út (`0x007fde80`) a `0x007fd800`-nak adja a `qshow+0x2f8` objektumot és a pontot; a `0x007fd800` találatkor a kiválasztott `0xf8` bájtos rekord első dwordját adja kimenetül, de a caller csak az `EAX=0` visszatérési ágban továbbítja ezt az értéket az `0x008018a0`-nak (`0x007fe322`-`0x007fe33e`, `0x007fd899`-`0x007fd8a9`). A `0x004b0190` az állapotobjektum `[+0xc4]` mezőjéből indul; annak `+0x48` másodlagos vtable `+0x2c` helyét hívja az indexszel és a kimeneti descriptor címével (`0x004b01dd`-`0x004b01f2`). A `0x004a5710` az állapot `[+0xc4]` mezőjét az alkalmazás `[+0x1034]` objektumával tölti (`0x004a572e`-`0x004a5739`); a `0x00402f90` ezt az objektumot a `0x00415790` konstruktorral hozza létre. A konstruktor az elsődleges vtable-t `0x00c81f78`-ra, a `+0x48` alobjektum vtable-jét `0x00c81fa4`-re állítja (`0x004157fd`, `0x00415804`). Az RTTI-index a `0x00c81f78` címet `CThumbDB`-ként azonosítja, a `0x00c81fa4+0x2c` vtable-hely pedig `0x004406f0`-ra mutat.

A `0x004406f0` második paramétere az index, harmadik paramétere a kimeneti `CSlice`; az `0xffffffff` indexet `-1`-gyel utasítja el. Egyébként a CThumbDB másodlagos `+0x48` interfészén belüli `[this+0xb00]` lista indexelt eleméből veszi a tokent (a listán kívüli indexnél ugyanennek az interfésznek a `[this+0xb04]` mezőjét használja), majd a token sztringjét a `0x004dca40`-nek adja a `CSlice` kitöltéséhez (`0x004406f0`, Ghidra-C és ellenőrző diszasszembly). A `0x004dca40` a CIndexer hash-táblájában keresi a szót; találatkor a `CSlice+0x60` mezőbe a szót, a `+0x64` mezőbe annak posting listáját, a `+0x5c` mezőbe pedig az indexet írja (Ghidra-kimenet: `2026-10-21-idorend-28.txt`, `0x004dca40`). A qshow az így visszakapott `+0x64` listát járja be, és az elfogadott indexeket az eredeti lista sorrendjében fűzi a saját `+0x3ec` tömbjébe (`0x00801964`-`0x00801bd5`).

**B út - független album-sorrend adatút.** A `docs/specs/album-sorrend.md` 2.1 és 2.4 szakasza, a qshow-függvénytől független album-rendezési hívási úton, ugyanazt a `CThumbDB` másodlagos vtable (`0x00c81fa4`) `+0x2c` helyet azonosítja a `0x004406f0` függvényként. Ott a `CSlice+0x64` a `]album:<token>` CIndexer-szó rekordindex-listája; annak sorrendjét a Picasa a `wordhash.dat`-ban tárolja és visszatöltéskor átrendezés nélkül másolja. A két út egyezik abban, hogy a qshow indexelt tokent kér le, majd annak `CSlice` posting listáját sorrendtartóan dolgozza fel. Ez **megerősíti az adatút és a listabejárás mechanizmusát**, de nem azonosítja, hogy a qshow `+0x50c` indexe futás közben mely tokenre mutat, és a posting-list indexei közül melyik lesz ténylegesen látható kép.

##### §2 A qshow billentyűi és az automatikus lejátszás hívásútja

A `0x008037e0` állítja elő a qshow `QDrawable` objektumát, és a `0x007fa7f0`-nel hozza létre az oneup-objektumot. A `0x007fa7f0` a `0x00cbd66c` (`QDrawable::vftable`) vtable-t állítja be; ennek indexelt metóduslistájában a `+0x30` slot címe `0x00801270`. Ez és a közvetlen utasításolvasás egymástól függetlenül köti a `0x00801270`-et a qshow billentyűkezelőjéhez.

A `0x00801270` csak `WM_KEYDOWN` (`0x100`) üzenetet dolgoz fel; a nulla és `WM_CHAR` (`0x102`) üzenet visszatér. A billentyűágak:

| Billentyű | Bináris hívásút | Pontos határ |
|---|---|---|
| Escape (`0x1b`) | `0x00801270` → `0x007fb820` | A jelenlegi objektum vtable `+0x24` getterét hívja; a qshow-építő által beállított cél a `qshow` nevű `ytWindow` gazdaablak (`0x00982bf0`, vtable `0x00cd87fc`), ennek `+0x14` slotja `0x00983270`, amelyet `(0,0)` argumentummal hív (`0x007fb998`-`0x007fb9df`). A gazdaablak-metódus végső navigációs hatása és a visszaállított nézet/pozíció nyitott. |
| Bal (`0x25`) / fel (`0x26`) | `0x00801270` → belső ág `0x008014bc` → `0x008011b0` | Timeline módban a `0x007fd0c0`-t hívja a `[this+0x2f8]+0x30` értékével és a bináris `0x00cf3a48` címen tárolt `2.0f` értékkel. Ez az argumentumirány; a látható képek térbeli iránya a `0x007fd0c0` teljes állapota nélkül nincs meg. Timeline módon kívül, ha `[this+0x3bb] != 0`, a `0x00802980` előző-eleme út fut; egyébként a `0x00802ae0` hívódik. |
| Jobb (`0x27`) / le (`0x28`) | `0x00801270` → belső ág `0x008014ac` → `0x00801210` | Timeline módban a `0x007fd0c0` hívás ugyanazt a mezőt adja át, de `-2.0f` argumentummal. Timeline módon kívül, ha `[this+0x3bb] != 0`, a `0x008029f0` következő-eleme út fut; egyébként a `0x00802a90` hívódik. |
| Szóköz (`0x20`) | Ha `[this+0x3bb] != 0`, a `0x00803110` hívódik `[this+0x2dc]` argumentummal; ha nulla, a `0x00801130` hívódik. A külön Ctrl-ág `[this+0x3ba]=1`-et ír és `0xf4240`-t ad vissza. | A módváltás állapotfüggő: a `+0x3bb != 0` ág a 0-s diavetítési módba állít; a nulla ág csak a `+0x3bb` állapotkezelőjét hívja. Részletek és a két bináris út: 38.2.65. A visszatérési nézet és index nyitott. |

A handler további ágakat is tartalmaz a `0`-`9` és a Ctrl+`F`/`B`/`O` billentyűkre; ezek pontos felhasználói jelentése ebben a körben nincs feltárva. Home/End (`0x23`/`0x24`) explicit ága nincs.

A `0x008032e0` név szerinti eseménykezelőjében a `oneup/auto` és `oneup/auto2` a `0x00803110`-et hívja; a `oneup/timeline` a `0x00802be0`-t, majd a `0x007fda00`-t. A `oneup/exit` a tulajdonos vtable-jának `+0x24` függvényétől kért objektum vtable-jának `+0x14` függvényét hívja két nulla argumentummal. A `0x008037e0` a `0x00982bf0`-gel létrehozott `qshow` gazdaablakot (RTTI-adatszimbólum: `ytWindow::vftable`, `0x00cd87fc`) a oneup `+0x50` mezőjébe állítja (`0x00803977`-`0x0080397f`, setter: `0x007fa480`); a `ytWindow` vtable `+0x14` slotja a `0x00983270`. Az Escape `0x007fb820` és a gomb Exit útja így ehhez a gazdaablak-metódushoz jut `(0,0)` argumentummal (`0x007fb998`-`0x007fb9df`, `0x0080355d`-`0x00803573`). A visszatérő objektum azonosított, de a gazdaablak-metódus végső navigációs hatása és a folytatási nézet/pozíció nyitott. Az `overlays/startbutton` név azonossága a `oneup/auto` eseménnyel nincs bizonyítva. A `0x007fb210` az `overlays/timeline`, `overlays/timelinedot` és `overlays/sliderthumb` elemeket kéri le; ez az elemneveket és létrehozásukat igazolja.

A qshow egérkezelője a `0x007fde80`. Timeline módban bal gomb lenyomásakor (`WM_LBUTTONDOWN=0x201`) a vezérlő téglalapjai alapján állítja a `[this+0x429]` húzásjelzőt vagy a `[this+0x428]` másik sávjelzőt. A húzáság azonnal meghívja a `0x007fdd00` csúszka-leképezőt; húzás közbeni egérmozgás ugyancsak oda jut. Egérfelengedéskor (`WM_LBUTTONUP=0x202`) a húzáság a `0x007fd770`-nek adja át a `[this+0x514]` indexet, majd törli a két jelzőt. A sávjelző további hatása és a `0x007fd770` felhasználói jelentése nincs teljesen azonosítva. A `0x007fb210` az `overlays/timeline`, `overlays/timelinedot` és `overlays/sliderthumb` elemeket kéri le; a `timelinedot`, `startbutton` és listaikon teljes kattintási/húzási működése továbbra sem következik az elemnevekből.

Az automatikus léptetés küszöbe korábban megerősítve lett: a `0x00802060` a QPC-ből számolt eltelt másodpercet a `Preferences\SlideshowEffectTime` egész másodpercben megadott `T` értékével hasonlítja össze, és a túllépéskor léptető utat hív. A callback frissítési periódusa és az aktív futásidejű `T` nincs meg; a pumpa 50 ms-os alvása legfeljebb 20 frissítést/másodpercet ad, ha a jelző be van állítva. A `T` küszöb ezért nem azonos a bizonyított, állandó automatikus léptetési ütemmel (38.2.34 §1, §3; 38.2.34 §5 cáfoló ellenőrzése).

##### §3 A dátumcsúszka képernyőkoordináta-leképezése

A `0x007fdd00` az egér x koordinátáját a `[this+0x6d8]` és `[this+0x6d8]+[this+0x6c8]` közötti szakaszra korlátozza, majd `t=(x-lo)/(hi-lo)` normalizált értéket képez. Az `A` tömb `[this+0x388]`, az elemszám `[this+0x38c]>>1`; minden indexnél az `A[i]/A[n-1]` arányt hasonlítja `t`-hez, és a legkisebb abszolút eltérésű indexet választja. A feltétel szigorú `<`, így azonos eltérésnél az első talált index marad. A választott index a `[this+0x514]` mezőbe kerül; az indexelt elem pointere a `[this+0x3a8]+i*0xf8` címről lesz kiválasztva, ha `i < [this+0x3ac]>>1`, különben a kijelölt pointer nulla. A thumb x koordinátáját a `0x00c29990` helper eredménye és a `[this+0x728]` mező alapján frissíti, az y-t a `[this+0x72c]` mezőről állítja vissza.

**Korlát.** Az `A` tömb elemeinek jelentése nincs meg; a kód önmagában nem bizonyítja, hogy azok dátumok, Unix-idők vagy más időkoordináták. Ezért a képernyő x → normalizált arány → tömbindex leképezés pontos, a dátumérték leképezése és az eredeti adatmező nincs meg. A `0x00c29990` helper teljes kerekítési viselkedése sincs e körben feloldva.

##### §4 Bizonyíték, független utak és cáfoló kísérlet

| Állítás | Forrás |
|---|---|
| A `CThumbUI+0x2bc` mezőbe tett objektum `CThumbDB`; ez különbözik a qshow inputjától. | bináris (`0x004039f0`, `0x005643e0`, `0x00415790`) + RTTI (`0x00c9052c`, `0x00c81f78`) |
| A qshow bemeneti pointerlánca a `CThumbUI+0x2c0` mezőtől oneup `+0x2f4`-ig. | bináris (`0x005e96d9`, `0x008037e0`, `0x007fa7f0`, `0x008018a0`) - feltételes, egy közvetlen adatút |
| A MakeTimeline count/index út a `CThumbUI+0x2c0` mezőt használja; az elemkérő vtable-hívás külön `+0x2bc` szolgáltatóhoz jut. | bináris (`0x005e9434`, `0x005e9490`, `0x00562cc0`) + RTTI (`0x00c81f78`) |
| A qshow `[+0x2f4]` állapotobjektumának `[+0xc4]` mezője a CThumbDB-re mutat; a `+0x48` alobjektum `+0x2c` vtable-helye a `0x004406f0` token→CSlice lekérdező. | bináris (`0x00402f90`, `0x004a5710`, `0x00415790`, `0x004b0190`, `0x004406f0`) + RTTI/vtable (`0x00c81f78`, `0x00c81fa4`) |
| A `0x004406f0` az átadott indexhez tokent keres, a `0x004dca40` pedig a találat `CSlice+0x64` posting listáját állítja be. | bináris (`0x004406f0`, `0x004dca40`; Ghidra-C és eredeti PE diszasszemblálás) |
| A qshow az adott `CSlice+0x64` listát indexsorrendben járja be, kizárás után az elfogadott listaértékeket a `+0x3ec` tömbbe fűzi; a builder nem rendez. | bináris (`0x008018a0`, `0x004b0190`) |
| Az albumtoken `CSlice+0x64` listája a megjelenítési sorrend hordozója; a `wordhash.dat` ezt menti és betöltéskor sorrendtartóan másolja. | bináris (`album-sorrend.md` 2.1, 2.4; több külön album-rendezési út) |
| A `+0x50c`-nek átadott érték induláskor 0; frissítéskor a qshow `+0x2f8` adatobjektumának kiválasztott `0xf8` rekordja első dwordja, amit a `0x004406f0` indexként használ. | bináris (`0x008037e0`, `0x00801cb0`, `0x007fd8c0`, `0x007fde80`, `0x007fd800`, `0x004406f0`) |
| Az indexelt token konkrét értéke/típusa, a posting-list indexek képfájlokra oldása, a gyűjtemények és a fotó metaadatából származó dátumkulcs. | NINCS MEG |
| A `0x00801270` a QDrawable qshow-objektum billentyűkezelő-helye; Escape, nyilak és szóköz közvetlen híváságai a táblázat szerintiek. | bináris (`0x00801270`, `0x007fa7f0`) + RTTI (`0x00cbd66c`) |
| A csúszka x→index képlete, a kiválasztott mezők és a szigorú tie-kezelés. | bináris (`0x007fdd00`) |
| A csúszka húzás- és felengedési útja a qshow egérkezelőjéből a leképezőig, majd a `0x007fd770`-ig. | bináris (`0x007fde80`, `0x007fdd00`, `0x007fd770`) |
| A gomb Exit és Escape visszatérő objektuma a `0x00982bf0` által létrehozott `qshow` `ytWindow` host; oneup `+0x50` → host `vtable+0x14` (`0x00983270`). | bináris, két külön Exit/Escape hívásút (`0x008037e0`, `0x00982bf0`, `0x007fa480`, `0x007fb820`, `0x008032e0`, `0x00983270`) + RTTI/vtable (`0x00cd87fc`) |
| A `+0x2c0` és `+0x388` mezők közvetlen íróinak célzott keresése nem kötötte az összes azonos offset-találatot a qshow/QDrawable osztályhoz. | bináris (`paszta.py` `.text`-pásztázás; `paszta.memoria_kapu()` volt az első művelet) |
| Az `A` tömb dátumjelentése, a teljes gyűjteményi forrás és a konkrét elemkészlet. | NINCS MEG |
| A teljes képkockánkénti pálya, a rétegek/képtartalom, a `timelinedot`/listaikon teljes vezérlése, valamint a qshow host metódusának végső navigációs hatása és a visszaállított nézet/index. | NINCS MEG |
| E körbeli futásidejű qshow-képkocka-felvétel vagy QEMU-kimenet. | NINCS MEG |

**A két független út.** A út: a qshow induló hívója 0-t ad át, az automatikus frissítés és az egér-találat pedig a qshow `+0x2f8` adatobjektumának kiválasztott rekordja első dwordját adja át; ezt a `0x008018a0` → `0x004b0190` → `CThumbDB+0x48` vtable `+0x2c` → `0x004406f0` → `0x004dca40` út indexként, tokenként és `CSlice` posting listájaként kezeli. B út: az ettől független album-rendezési lekérdezésben a `album-sorrend.md` 2.1/2.4 a CThumbDB másodlagos vtable `+0x2c` helyet ugyanahhoz a `0x004406f0`-hoz köti, majd a `CSlice+0x64` listát a `wordhash.dat` sorrendhordozójaként azonosítja. A két út egyezik a vtable-hely, lekérdező és listamező szerepében; **megerősített** a rekord-dword → CThumbDB-tokenindex → `CSlice` mechanizmus, valamint a qshow lista szűrés utáni sorrendtartása. Az indexelt token konkrét tartalma/típusa, a posting-list indexek konkrét képei és a dátum szerinti kulcs nem bizonyított.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a qshow a token posting-listáját sorrendtartóan viszi át a saját `+0x3ec` listájába, és külön dátumrendezést végez. Az `0x008018a0` teljes utasítássorában a ciklus a posting-list indexét 0-tól növeli, az elemeket csak a párhuzamos kizárási feltétellel hagyja ki, és nem hív összehasonlítót vagy rendezőt; ezt a Ghidra-C hurokja is ugyanígy mutatja. Független ellenőrzésként a `0x004406f0`/`0x004dca40` adatút és az album-rendezési út `album-sorrend.md` 2.1/2.4 szakasza ugyanazt a `CSlice+0x64` listát azonosítja. A próba **nem cáfolta** a builderen belüli sorrendtartást; azt cáfolta, hogy a `0x008018a0` önálló dátum szerinti rendezőt tartalmaz. Nem cáfolja, hogy a megjelenítés animációs időkoordinátája, a token kiválasztása vagy más későbbi render-ág dátumhoz kötött lehet. A negatív komparátoreredmény csak a teljesen áttekintett `0x008018a0` függvényre áll, nem globális `.text`-negatív állítás.

**Cáfoló kísérlet.** Azt a feltevést próbáltam cáfolni, hogy a főablak `0x005e60d0` kezelője maga a qshow billentyűkezelője, és hogy a nyilak minden állapotban közvetlenül előző/következő képet léptetnek. A `0x00801270` közvetlen diszasszemblálása a `WM_KEYDOWN` ágat és a timeline módú `0x007fd0c0` hívást mutatja; a QDrawable vtable `0x00cbd66c` metóduslistája a `0x00801270`-et a `+0x30` eseményhelyre teszi. A `0x005e60d0` Ghidra-kimenete külön főablak-kezelő. A próba megcáfolja mindkét feltevést; a címosztályozást az assembly és az attól független RTTI/vtable út egyaránt alátámasztja.

**Bizonyítottsági fok.** A teljes #5401 **nyitott**. A `CThumbUI+0x2bc` mezőbe tett objektum `CThumbDB` osztálya, a gomb Exit/Escape célobjektuma (`qshow` `ytWindow`) és a QDrawable billentyűkezelő-helyének besorolása **megerősített** (külön vtable/callback-út + RTTI/vtable-adat). A qshow közvetlen bemeneti pointerlánca (`CThumbUI+0x2c0` → oneup `+0x2f4`) egy közvetlen statikus adatútból ismert, ezért **feltételes**; a `+0x2c0` mögötti kollekció szemantikája **nyitott**. A §1/a szerinti indexforrás (kezdetben 0, utána a qshow `+0x2f8` adatobjektum kiválasztott rekordjának első dwordja), CThumbDB-token→`CSlice` út és az elfogadott posting-list elemek sorrendtartó átvitele **megerősített**; az indexelt token tartalma és típusa nyitott. A közvetlenül olvasható billentyű-, egér- és csúszka-utasítássorok felhasználói hatása **feltételes**, mert hiányzik a gyűjteményt megnevező út és a vizuális mérés. A §38.2.34 automatikus léptetési `T` küszöbe ismert, a tényleges periódus nem; a §38.2.61-62 mozgás-részletei nem zárják le a teljes, képkockánkénti animációt.

##### §5 A #5401 „Kész, ha” pontjainak állapota

1. ⛔ **Képlánc, forráshalmaz, sorrend, gyűjteményenkénti darabszám és elemlista:** megerősített, hogy a qshow kezdetben 0 indexet, frissítéskor pedig a qshow `+0x2f8` adatobjektum kiválasztott `0xf8` rekordjának első dwordját használja CThumbDB tokenindexként, és annak `CSlice+0x64` posting listájából szűrés után sorrendtartó elemlistát épít (`0x008018a0`, `0x008037e0`, `0x00801cb0`, `0x007fd8c0`, `0x007fde80`, `0x007fd800`, `0x004b0190`, `0x004406f0`, `0x004dca40`; albumtoken-lista: `album-sorrend.md` 2.1/2.4). Az indexelt token konkrét tartalma, a posting-list értékeinek tényleges képei, a dátumkulcs és kollekciónkénti darabszám **NINCS MEG**.
2. ⛔ **Pálya, méret, forgatás, alfa, időzítés, háttér és kártyarajz:** a 38.2.34, 38.2.61 és 38.2.62 igazolt részképletei mellett hiányzik a teljes képkocka → transzformáció → rajzréteg lánc és az élő képkockafelvétel. E körben nem állítok teljes mozgásképletet.
3. ⛔ **Vezérlők:** a billentyűágak, csúszka húzás/felengedés útja és normalizált indexképlete részben megvan; a dátumtömb jelentése, a `timelinedot`, `startbutton`, listaikon és automatikus lépés tényleges periódusa nyitott. Az Exit/Escape a qshow `ytWindow` host `0x00983270` metódusához jut; a végső navigációs hatás nincs meg.
4. ⛔ **Diavetítésbe lépés és kilépés:** a Space két állapotágát és a `+0x3b8=0` átmenetet a 38.2.65 részletezi; a futásidejű előfeltétel és az Escape utáni gyűjtemény/index nyitott. Az automatikus léptetés `T` másodperces küszöbe ismert; az Exit/Escape célobjektuma a qshow `ytWindow` host, de a gazdaablak-metódusának végső képernyője és a tényleges callback-periódus nincs bizonyítva.

##### §6 Nyitott

- A `CThumbUI+0x2c0` mező egy CThumbUI-adatútban olvasott; a `0x005643e0` konstruktor `[this+0x2c0]` mezőjébe az EAX-ben kapott értéket írja (`0x005644fa`), a `0x004039f0` pedig a konstruktor `+0x2c0` argumentumát a hívó `[X+0x1038]` mezőjéből adja. A teljes `.text` offset-pásztázás sok más osztálybeli `+0x2c0` találatot is ad, ezért a konkrét írók osztályhoz kötése nélkül azok nem nevezhetők meg. Nyitott: a `[X+0x1038]` érték forrása és a kollekciójelentés; megszerzés: az `0x004039f0` szülőobjektumának azonosítása és a `[X+0x1038]` mezőíróinak `paszta.py`-jal, `memoria_kapu()` elsőként történő célzott pásztázása.
- A `+0x50c` tokenindex adatforrásának hívásútja ismert: kezdetben 0; frissítéskor a qshow `+0x2f8` adatobjektuma kiválasztott rekordjának első dwordja, amit a `0x007fd8c0` időfüggő kiválasztása vagy a `0x007fd800` egér-találata ad (`0x0080394f`-`0x00803953`, `0x00801ccf`-`0x00801ce5`, `0x007fe322`-`0x007fe33e`). Nyitott a rekord első dwordjának megfelelő konkrét token és a `0xf8` rekordok upstream forrása; megszerzés: a `0x007fc010` építő adatútjának és a rekordlista feltöltőinek követése, majd a tokenlistával való egyeztetése.
- A qshow `+0x388` pointer közvetlen íróját a `paszta.py` teljes `.text` pásztázása nem rendelte hozzá a QDrawable osztályhoz; ugyanaz az eltolás más osztályokban is előfordul. Az `A[i]`/`A[n-1]` értékek időbeli jelentése NINCS MEG. Megszerzés: a QDrawable vtable ismert metódusainak célzott ellenőrzése, majd a talált segéd- vagy helyfoglaló út `+0x388`-ra író kódjának osztályhoz kötése.
- A `0x007fd0c0`, `0x00802ae0`, `0x00802a90` és `0x007fde80` dekompilálása elkészült; a qshow `+0x2f8` adatobjektuma látható eredménye, a nem timeline bal/jobb ág felhasználói jelentése, a `+0x428` sávjelző és az overlay-nevek egér-hit-testhez kötése továbbra is nyitott.
- A gomb Exit és Escape visszatérő objektuma a qshow `ytWindow` host; a `+0x14` metódus `0x00983270` végső navigációs hatása és a visszaállított nézet/index NINCS MEG.
- A `0x00983270` dekompilálása elkészült: a nulla paraméterű ág WM_CLOSE-t kér a qshow `+0x6c` HWND-jére, a másik ág az aktuális szál ablakait járja be. A képernyőn megjelenő visszatérési állapotot és a megőrzött kollekció/indexet csak futás közbeni, előtte-utána felvétel dönti el.
- Futás közbeni megerősítés: qshow Exit/Escape előtt és után rögzíteni a megjelenő ablakot, kollekciót és elemindexet; ez a `0x00983270` statikus olvasatát ellenőrzi.
- A `0x009dc040` dekompilálása és QEMU-ellenőrzése elkészült (38.2.64); nyitott a hívók képpuffer- és rétegszemantikája, valamint a `0x008001c0` → `0x00aa6180` rétegsorrend.
- A `0x00802ae0` és `0x00802a90` közvetlen mezőhatása a 38.2.66-ben rögzítve; hogy a pufferürítés és az `+0x3f4` változása milyen felhasználói eredményt ad, NINCS MEG.
- A `0x007fde80` koordináta-, egérüzenet- és flag-ágai a 38.2.66-ben rögzítve; a `+0x428`/`+0x429` vezérlők `timelinedot`/`sliderthumb` nevű overlayhez rendelése és a listaikon hit-testje NINCS MEG.
- QEMU-val számszerűen vezérelt qshow-futás és sűrű, igazoló Wine-képkocka-felvétel NINCS MEG; megszerzéséhez a forráskollekciót és az aktív lejátszási állapotot rögzítve kell futtatni.

**Új kutatási jegyjavaslat.** Nincs; mindegyik nyitott tétel a #5401 négy elfogadási pontjához tartozik.

#### 38.2.64 A Space/Auto objektumváltása, kilépés és alfa-keverés (#5401, 2026-10-22)

**Hatókör és módszer.** A `0x00801130`, `0x00803110`, `0x00802be0`, `0x00983270` és `0x00982fa0` függvényeket az eredeti PE-ből annotált helyi diszasszemblálással ellenőriztem; a SQLite-index függvényméreteit használtam. A `0x00801130` és `0x00983270` Ghidra-kimenetét külön összevetettem az utasításokkal. A `0x00983430` (qshow-host méretező/frissítő út) és a `0x008032e0` név szerinti Auto/Auto2 ágának meglévő dekompilálását szintén felhasználtam. A 202-209 és 210-216 Ghidra-kör a korábbi címkérések dekompilálását elvégezte; a mostani nyitott pontokhoz új, ismert függvényhatárú Ghidra-cím nem szükséges. QEMU-mérés a `0x009dc040` alfa-keverőn készült az eredeti gépi kódon; a próba-bemenetek és kimenetek lent. Wine/qshow élő felvétel ebben a körben nem készült; a korábbi job-220 felvétel nyers képei nem voltak a helyi mérőadat-archívumban.

##### §1 Space és Auto: pontos állapot- és objektumút

`0x00801270` a szóköz-ágban a `[this+0x3bb]` állapottól függően hívja a `0x00803110`-et vagy a `0x00801130`-at. A `0x00803110` az átadott oneup-objektum `[+0x25c]` belső objektumán dolgozik: ha `[+0x3be] != 0`, előbb `0x00801cf0`-et hív; beállítja `[+0x518]=1`-et, QPC-értéket ír `[+0x520]`-ba, majd nullázza `[+0x3b8]`-at és `[+0x428]`-at. Ezután meghívja a `0x00801130`-at a belső objektumon. Ha a oneup `[+0x50]` hostmezője nem nulla, a `0x00802be0`-nek a hostot és a `[+0x25c]` belső objektumot adja át.

A `0x00802be0` a host `[+0x64]` aktív objektumát cseréli: a korábbi objektum vtable `+0x28` metódusát null argumentummal hívja, beírja az új pointert, majd annak vtable `+0x28` metódusát a host pointerével hívja. Ezután `0x00983430`-at hívja. Az utóbbi a `[host+0x6c]` HWND kliensméretét kéri le, `0x00983a60`-on át méretet közöl, és teljes frissítést kér az aktív objektumtól. A közvetlen út tehát hoston belüli objektumváltás és újraméretezés/újrarajzolás; a `0x00803110` törzsében nincs közvetlen ablaklétrehozó API-hívás.

A `0x00801130` a `[this+0x3bb]` logikai értékét megfordítja, majd átadja a `0x0097e510`-nek. Ha az új érték nulla, `0x00802230(this,0)`-at és a `0x009aabf0(this+0x444,-1,-1,-1,-1)` útvonalat hívja; ha nem nulla, `0x00802c20`-at hív, és `[this+0x3ba]==0` esetén a `0x00aa6f40`-hez jut. A `0x008032e0` név szerinti eseménykezelőjében mind a `oneup/auto`, mind a `oneup/auto2` a `0x00803110`-et hívja. Ezért a `0x00803110` önmagában nem kizárólag a Timeline→diavetítés billentyűparancs: a statikus kód több bemenetről is eléri.

**A futásfelvétel határa.** A 38.2.17 § job-220 feljegyzése szóköz után a kártya gyűjteményének teljes képernyős diavetítését, majd Escape után a főablak megjelenését írja le (képkockaszámokkal). A nyers képkockák ebben a munkamenetben nem elérhetők, ezért ezt korábbi, nem újramért mérési bizonyítékként tartom nyilván. A statikus `0x00803110` út nem adja meg a visszatérő gyűjteményt vagy képpozíciót.

##### §2 Kilépés a qshow gazdaablakból

Az Escape út (`0x007fb820`) és a név szerinti `oneup/exit` ág (`0x008032e0`) külön hívási útból a oneup `[+0x50]` mezőjének vtable `+0x14` metódusát hívja. A `0x008037e0` ezt a mezőt a `0x00982bf0` által létrehozott `qshow` `ytWindow` hosttal tölti fel; a host vtable `+0x14` célja `0x00983270`.

A `0x00983270` nulla első paraméterénél a `[this+0x6c]` HWND-re `PostMessageA(hwnd, WM_CLOSE=0x10, 0, 0)`-t küld, ha a `DAT_00d67858` globális értéke nem pozitív. Pozitív értéknél `GetCurrentThreadId()` + `EnumThreadWindows()` út fut a `0x00982fa0` callbackkel, és beállítja a `DAT_00d6784b` jelzőt. A függvény tehát bezárási/ablak-enumerációs út, nem olyan helyi index-visszaállítás, amelyből a folytatási gyűjtemény vagy kép megnevezhető lenne.

##### §3 Alfa-keverő: számszerű, QEMU-val ellenőrzött képlet

Az `0x009dc040` az alfa egész értékét előbb `a0=max(a-1,0)` alakra csökkenti, a kiegészítő súlyt `255-a0`-ként képezi, majd a két forráscsatorna súlyozott összegét 8 bittel jobbra tolja. `a` 0 és 256 közötti egész tesztértékekre, csatornánként `O=floor((a0·X+(255-a0)·Y)/256)`. A `DAT_00d695d4` kapcsoló a tesztelt ágakban az `X` és `Y` forrást felcseréli. A leolvasott bináris utasítások és az eredeti függvény QEMU-kimenete egyezik. Példamérés két BGRA pixelre (a két forrás bájtjai `20,40,60,80,100,120,140,160` és `220,200,180,160,140,120,100,80`):

| `DAT_00d695d4` | `a` | QEMU-kimeneti bájtok |
|---:|---:|---|
| 0 | 0, 1 | `219,199,179,159,139,119,99,79` |
| 0 | 128 | `119,119,119,119,119,119,119,119` |
| 0 | 255 | `20,40,60,80,99,119,139,159` |
| 0 | 256 | `19,39,59,79,99,119,139,159` |
| 1 | 0 | `19,39,59,79,99,119,139,159` |
| 1 | 128 | `119,119,119,119,119,119,119,119` |
| 1 | 255 | `218,198,178,159,139,119,99,80` |
| 1 | 256 | `219,199,179,159,139,119,99,79` |

Ez a keverő műveletét és a forrásirány kapcsolását igazolja a fenti bemeneteken; a hívók által átadott alfa-tartományt, a tényleges qshow-pufferek szerepét és a háttér/kártya rétegsorrendet nem azonosítja (`0x00aa6180`, `0x008001c0`).

##### §4 Két út, cáfoló ellenőrzés és bizonyítottság

**A út: utasítás- és hívási lánc.** A `0x00801270` → `0x00803110`/`0x00801130` ág, a `0x00803110` → `0x00801130`/`0x00802be0` hívások, a host `+0x64` objektumcseréje, valamint a `0x00983270` WM_CLOSE-ág az annotált diszasszemblálásból követhető. A qshow host vtable `+0x14` célját az `0x008037e0` konstrukciós útja és a host vtable adata köti `0x00983270`-hez.

**B út: független ellenőrzés.** A `0x008032e0` név szerinti Auto/Auto2 összehasonlító ágai a `0x00803110`-hez vezetnek; ettől függetlenül az Escape-út és az Exit-gomb útja külön-külön a oneup `[+0x50]` gazdaablak-objektum `vtable+0x14` célját hívja. A qshow felépítője ugyanebbe a `[+0x50]` mezőbe írja a `qshow` `ytWindow` hostot. Ezek a statikus utak a hoston belüli objektumváltással és bezárási kéréssel egyeznek. A teljes képernyős megjelenést és főablakba visszatérést a korábbi job-220 felvétel külön, futásidejű útként rögzíti, de a nyers kép hiánya miatt most nem auditálható újra.

**Cáfoló kísérlet.** Azt az olvasatot próbáltam cáfolni, hogy a `0x00803110` maga új Win32-ablakot hoz létre. A teljes 107 bájtos függvényt diszasszembláltam: ablaklétrehozó API-hívás nincs benne; az utolsó út a `[+0x50]` host és a `[+0x25c]` tartalomobjektum `0x00802be0`-n keresztüli cseréje. Ezt függetlenül a `0x00983430` törzse is alátámasztja: a függvény HWND-kliensméretet kér le, méretez, majd újrarajzolást kér. A cáfoló próba azt a túl erős állítást igazolja, hogy a `0x00803110` közvetlen ablaklétrehozó; nem cáfolja, hogy a host új tartalomobjektuma vizuálisan diavetítésként jelenik meg.

**Bizonyítottsági fok.** A qshow `ytWindow` host és a `vtable+0x14` → `0x00983270` kilépési út **megerősített**: a hostot a konstrukciós/vtable-adat azonosítja, és az Escape, illetve az Exit külön hívási útja is ezt a slotot éri el. A `0x00803110` belső mezőmódosításai és hívássorrendje **feltételes** (egy közvetlen függvényút); az Auto/Auto2 külön név szerinti hívói ezt a függvényválasztást, a korábbi job-220 felvétel pedig csak a látható átmenet feljegyzett eredményét támasztja alá. Az alfa-keverő képlete a megadott QEMU-bemeneteken **megerősített** (utasítások + eredeti gépi kód mért kimenete). A Space utáni teljes képernyős diavetítés és Escape utáni főablak a korábbi job-220 feljegyzés alapján **feltételes** ebben a munkamenetben, mert a nyers képkockák hiányoznak. A teljes #5401 **nyitott**: a forráshalmaz és rendezés, teljes képkockánkénti pálya/rajz, vezérlők dátumjelentése és periódusa, valamint a visszatérő képpozíció továbbra sincs lezárva.

##### §5 A PicasaPy jelenlegi Időrendje és fejlesztési határ

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `0x005e8a70` Időrend útja oneup/qshow bemutatót épít; Space a `0x00801270` állapotágán és a `0x00803110` host-objektumváltásán át jut a külön tartalomobjektumig. A gyűjtemény és a mozgás teljes képlete nyitott. | A `TimelineController.reload()` az index összes nem rejtett fotóját kéri le; a `picasapy.timeline.build_periods()` EXIF `taken_at`/befagyasztott fájlidő szerint év-hónapra csoportosít; a `TimelineView.qml` görgethető bélyegképrácsot rajzol, kattintásra a fő nézőt nyitja. Forrás: `src/picasapy/app/timeline_controller.py`, `src/picasapy/timeline.py`, `src/picasapy/app/qml/PicasaPy/TimelineView.qml`. | A #5377 teljes animált bemutatójának fejlesztői specifikációját csak a képlista, rendezés, mozgás/rajzréteg, vezérlők és visszatérési állapot lezárása után lehet pontosan megadni; a mostani bizonyíték nem ad becslésmentes, teljes implementációs listát. |

**Nyitott kérdések mérlege (38.2.64).** A Space/Auto és Exit statikus útja, valamint az alfa-keverő számszerű művelete már dokumentált. Nyitva marad a #5401 mind a négy elfogadási pontja: teljes képlánc; a képátmenet és rétegek teljes időfüggése; a timelinedot/startbutton/listaikon és dátumcsúszka tényleges jelentése, illetve autoplay periódusa; valamint a teljes képernyős diavetítésből visszaálló gyűjtemény és képpozíció.

#### 38.2.65 A szóköz állapotfüggő ága és a `+0x3b8=0` mezőírás (#5401, 2026-10-22)

**Hatókör.** Ez a szakasz a 38.2.63 szóköz-sorát pontosítja. Statikusan bizonyítható, hogy a szóköz nem minden állapotban ugyanazt a hívásutat hajtja végre. A `0x00803110` a `[edi+0x25c]` objektum `+0x3b8` mezőjét nullára írja; a 38.2.21 §4 Ghidra-eredménye azonosítja `edi`-t OneUpUI-ként, és `[edi+0x25c] = this` kapcsolatot rögzít, tehát az írás a qshow aktuális objektumán történik. A futásidejű kezdőállapotot és a kilépés utáni nézetet ez a kör nem mérte meg.

##### §1 A billentyűág és az állapotmódosítás

A `0x00801270` csak `WM_KEYDOWN` (`0x100`) esetén jut a billentyűágakhoz (`0x00801299`). A szóköz (`0x20`) vizsgálata a `0x008012df` címen történik. A külön Ctrl-ág után a `0x00801310` a `[this+0x3bb]` bájtot ellenőrzi:

- Ha a bájt nem nulla, a kezelő a `[this+0x2dc]` mezőt átadva meghívja a `0x00803110`-et (`0x00801310`-`0x0080131f`). A hívott függvény a `[oneup+0x25c]` állapoton: `esi`: ellenőrzi a `+0x3be` jelzőt; nem nulla értéknél előbb a `0x00801cf0`-et hívja. Ezután `+0x518=1`-et ír, lekéri a QPC-t, `+0x3b8=0`-t és `+0x428=0`-t ír, az időbélyeget `+0x520`-ba teszi, majd újrahívja a `0x00801130`-at (`0x0080311d`-`0x0080315c`).
- Ha a bájt nulla, a billentyűkezelő közvetlenül a `0x00801130`-at hívja (`0x00801332`-`0x00801334`), a `0x00803110` kihagyásával. A `0x00801130` a `+0x3bb` értékét nullára/nem nullára billenti, de a függvényben nincs `+0x3b8`-írás; ezért ez az ág önmagában nem bizonyít módváltást.

A frissen indított Időrendben a `0x007fda00` `[this+0x3bb]=0`-t állít be (38.2.9). A külön Ctrl-ágon kívüli **első Space** ezért a `0x00801130`-ra jut, és a `sete` művelet 1-re billenti a jelzőt; maga ez a függvény nem írja a `+0x3b8` mezőt. A `0x00802060` nem léptet, amikor a `+0x3bb` nem nulla (38.2.34). Ha a jelző a következő billentyűig nem változik, a **következő Space** a `0x00803110`-et hívja: ez a qshow `[this+0x3b8]` mezőjét nullázza, majd a `0x00801130` a `+0x3bb`-t ismét nullára billenti. A qshow-építő nulla módága a `0x00801cf0` diavetítési út. Az első Space által meghívott `0x00802c20` és `0x00aa6f40` belső/indirekt mellékhatásai nincsenek teljesen feltárva, ezért nem állítható, hogy kizárólag a második Space okoz minden látható módváltozást. Ez a statikus hívássor, nem futás közbeni képkocka-megfigyelés.

##### §2 A 0-s mód azonosítása és a független hívóút

A qshow-építő `0x008037e0` a paraméterrekord `+1` bájtja alapján választ: nulla esetén a `0x00801cf0`-et hívja (`0x008039de`-`0x008039fe`); nem nulla esetén a `0x007fda00`-t (`0x008039e2`-`0x008039e7`). A 38.2.9 szerint a `0x007fda00` a qshow saját `this+0x3b8` mezőjére `1`-et ír. A 38.2.21 §4 a `0x00803110` bemeneti objektumláncában `[edi+0x25c] = this`-t igazolja, ezért a Space-ág nullázása ugyanazon qshow-állapotmezőt éri el. A konstruktor nulla paraméterágának célfüggvénye a `0x00801cf0` diavetítési út; a nem nulla ága indítja az Időrend-módot.

**Független hívóút:** a `0x008032e0` név szerinti `oneup/auto` és `oneup/auto2` eseményágai külön-külön hívják a `0x00803110`-et (`0x00803486`, `0x008034c5`). Ez a billentyűkezelőtől független UI-belépési pont ugyanazt a módváltó rutint használja; a qshow-építő külön módválasztó ága a rutin által beállított nulla értéket a diavetítési úthoz köti.

Az átmenet nem bizonyít új ablak létrehozását: a `0x00803110` az állapotmezőket módosítja, és csak akkor hívja a `0x00802be0`-t, ha a oneup `+0x50` hostmezője nem nulla (`0x00803161`-`0x0080316e`). A korábbi job-220 feljegyzés szóközre teljes képernyős diavetítést ír, de az eredeti képkockasorozat és a `+0x3bb` kezdőértéke nem áll rendelkezésre; ez a megfigyelés itt nem függetlenül reprodukált mérés.

##### §3 Index és visszatérés

A `0x00803110` közvetlenül nem írja a `[state+0x3f4]` indexet. Ha a belépéskor `[state+0x3be] != 0`, az előtte meghívott `0x00801cf0` a `0x00801f25` címen eggyel csökkenti a `+0x3f4` értéket. A függvényútból ezért csak az állítható, hogy az index közvetlen írása hiányzik, de a feltételes előhívás módosíthatja; a tényleges kezdő index, a kilépéskori visszatérő elem és nézet **NINCS MEG**. A job-220 korábbi „visszatér a főablakba” megjegyzése nem azonosítja, hogy onnan az Időrend folytatódik-e.

##### §4 Bizonyíték, független utak és cáfoló kísérlet

| Állítás | Forrás |
|---|---|
| Szóközre a `[this+0x3bb] != 0` ág a `0x00803110`-et, a nulla ág közvetlenül a `0x00801130`-at hívja. | bináris (`0x00801270`, `0x00801310`-`0x00801334`) |
| A `0x00803110` a `+0x3b8` módmezőt nullára állítja; a feltételes előhívás `0x00801cf0`. | bináris (`0x00803110`, `0x0080311d`-`0x0080315c`) |
| A qshow módjelző bájt nulla értéke a `0x00801cf0`-hez, nem nulla értéke az Időrend `0x007fda00` útjához vezet. | bináris (`0x008037e0`, `0x008039de`-`0x008039fe`; 38.2.9) |
| Időrend-indításkor `[this+0x3bb]=0`; a nem nulla jelző mellett a `0x00802060` nem léptet. | bináris (`0x007fda00`; `0x00802060`; 38.2.9, 38.2.34) |
| A `oneup/auto` és `oneup/auto2` a billentyűúttól függetlenül ugyanazt a `0x00803110` rutint hívja. | bináris (`0x008032e0`, `0x00803486`, `0x008034c5`) |
| A `+0x3bb` nulla ágának `0x00801130` hívása nem ír `+0x3b8`-at. | bináris (`0x00801130`) |
| Az első flag-billentő ág helperlánca: `0x00801130` → `0x00802c20` és feltételesen `0x00aa6f40`; az utóbbi vtable `+0x84` hívást, a `0x00802c20` feltételesen `0x009833a0` host/callback útvonalat tartalmaz. | bináris (`0x00801130`, `0x00802c20`, `0x00aa6f40`, `0x009833a0`); az indirekt callbackek qshow-módra gyakorolt hatása NINCS MEG |
| A `+0x3f4` index csak a feltételes `0x00801cf0` előhívásban csökken; a visszatérési index/nézet. | bináris (`0x00801cf0`, `0x00801f25`); a futásidejű visszatérés NINCS MEG |
| A korábbi job-220 futásban a szóközt diavetítésbe lépésként jegyezték fel. | mérés (`job-220`; nyers képkockák és állapotbájt nélkül, nem reprodukált) |

**A két független út.** A út: a `0x00801270` billentyűágának nyers utasításolvasása és a `0x00803110` törzse megadja a feltételt, a `+0x3b8=0` írást és a flag visszabillentését (a `[edi+0x25c]=this` objektumkapcsolatot a 38.2.21 §4 dekompilációja adja). B út: a külön `0x008037e0` qshow-építő módjelző bájtja nulla esetén a `0x00801cf0` diavetítési ágat, nem nulla esetén a `0x007fda00` Időrend-indítást hívja; ez utóbbi a saját `[this+0x3b8]=1` és `[this+0x3bb]=0` mezőket állítja be (38.2.9). A két kódút ugyanazon qshow-objektum `+0x3b8` mezőjének 0-s diavetítési és 1-es Időrend-állapotát adja. A külön `0x008032e0` `oneup/auto`/`auto2` felületi ág ugyancsak a `0x00803110`-et hívja.

**Cáfoló kísérlet.** Azt a tág feltevést vizsgáltam, hogy a szóköz minden állapotból közvetlenül meghívja a módváltó rutint. Frissen indított Időrendnél a `0x007fda00` `[this+0x3bb]=0`-t állít be, ezért a Ctrl-ágon kívüli Space-re a `0x00801270` közvetlenül a `0x00801130`-at hívja; ez a közvetlen hívás nem a `0x00803110`. A feltevés, hogy minden Space ugyanarra a módváltó hívásra jut, cáfolva. Az `0x00801130` további helperjeinek indirekt, látható hatása ettől még külön nyitott.

**Bizonyítottsági fok: megerősített, szűk statikus hívásállításra.** A qshow `[+0x3bb] != 0` állapotában a Space a `0x00803110`-et hívja, amely a qshow `[+0x3b8]` mezőjét nullázza; a külön qshow-építő nulla módága a `0x00801cf0` diavetítési út. Friss Időrend-indításnál a flag 0-ról indul és a közvetlen első Space a `0x00801130`-at választja. Az első Space helperjeinek indirekt hatása, a futó állapot és a képkockákon látható váltás, valamint az Escape utáni visszatérés **nyitott**. QEMU- vagy új Wine-felvétel ebben a körben nem készült.

##### §5 A #5401 „Kész, ha” pontjainak frissítése

1. ⛔ **Képlánc és forráshalmaz:** ez a vizsgálat nem változtat a 38.2.63 nyitott megállapításain.
2. ⛔ **Teljes pálya és rajzolás:** a Space módágának feltárása nem egészíti ki a teljes képkockánkénti mozgást vagy a rétegrajzolást.
3. ⛔ **Vezérlők:** a szóköz egyik feltételes ága megvan; a dátumcsúszka, a `timelinedot`, a `startbutton`, a listaikon és az automatikus léptetés élő üteme továbbra is hiányos.
4. ⛔ **Diavetítésbe lépés és kilépés:** statikusan megerősített, hogy `+0x3bb != 0` esetén Space a módot nullázó `0x00803110`-et hívja; friss Időrend-indításnál a közvetlen első Space a flag-billentő ágat választja. Az első ág helperjeinek esetleges látható hatása, az élő előfeltétel, a képkockaeredmény, az Escape utáni nézet és a folytatási index nincs mérve.

##### §6 Nyitott

- Futásidejű mérés szükséges a szóköz előtt a `[this+0x3bb]`, a `[edi+0x25c]+0x3be` érték, utána a látható mód és `+0x3f4` index rögzítésére; a mérésen a `0x00801270` → `0x00803110` statikus út ellenőrizhető.
- A `0x00aa6f40` callback dekompilálási kérését a 38.2.66 §6 egyesíti a másik hívási út ugyanarra a címre vonatkozó kérdésével.
- A `0x009833a0` gazdaablak-callback út és a két `+0x28` cél a 38.2.67-ben fel van tárva; a közvetett segédfüggvény-hatásra nyitott címeket ott sorolja a Ghidra-várólista (`0x00aa6f40`, `0x00a56800`, `0x00a5e850`).
- A `0x00983270` gazdaablak-metódus statikus kilépési callbackje a 38.2.68-ban pontosított; hogy Escape után az Időrend melyik gyűjteménnyel és elemmel folytatódik, **NINCS MEG**.
- QEMU-val számszerűen vezérelt futás és sűrű Wine-képkocka-sorozat nem készült.

**Új kutatási jegyjavaslat.** Nincs; ezek továbbra is a #5401 elfogadási pontjai.

#### 38.2.66 Egérkoordináták, húzásjelzők és módfüggő nyílágak (#5401, 2026-10-22)

**Hatókör.** A `0x007fde80` egérkezelő már meglévő Ghidra-kimenetét az eredeti bináris függvényenkénti diszasszemblyével vetettem össze; a billentyűburkolókat és a két nem-automatikus háttérágat is közvetlenül olvastam. A vezérlőnevek és a látható eredmény futásidejű hozzárendelése ettől még nincs meg.

##### §1 Egérkoordináta és Timeline-módbeli húzás

A `0x007fde80` az esemény `x/y` koordinátáját a host kliensméretéből és a qshow `[+0x2c8,+0x2d0] × [+0x2cc,+0x2d4]` belső téglalapjából skálázza:

```text
x' = x_event * (([this+0x2d0] - [this+0x2c8]) / (client.right - client.left))
y' = y_event * (([this+0x2d4] - [this+0x2cc]) / (client.bottom - client.top))
```

Timeline állapotban (`[this+0x3b8] != 0`) balgomb-lenyomáskor (`WM_LBUTTONDOWN=0x201`) a `[this+0x6d8]`, `[this+0x6dc]`, `[this+0x6c8]`, `[this+0x6cc]`, `[this+0x718]`, `[this+0x728]`, `[this+0x71c]`, `[this+0x72c]` mezőkből ellenőrzési téglalapot képez. Az eredmény szerint a `[this+0x429]` húzásjelzőt állítja be és meghívja a `0x007fdd00` leképezőt, vagy a `[this+0x428]` jelzőt állítja be. Húzás közbeni egérmozgás (`WM_MOUSEMOVE=0x200`) a `+0x429` esetén ismét a `0x007fdd00`-hoz jut; a `+0x428` esetén a `[this+0x310]` értékét módosítja a kurzor x-eltéréséből és a `0x00cf3fa8`/`0x00cf3fb0` konstansokból.

Egérfelengedéskor (`WM_LBUTTONUP=0x202`) a `+0x429` ág a `[this+0x514]` értéket átadja a `0x007fd770`-nek, majd mindkét húzásjelzőt törli (`0x007fde80`, `0x007fe1a4`-`0x007fe1cf`). Az offset- és hívásút bizonyított; a `+0x428`/`+0x429` jelzők `timelinedot`/`sliderthumb` nevű overlayekhez rendelése, valamint a `+0x310` mező látható szerepe **NINCS MEG**.

Ugyanebben a kezelőben a `0x203` vagy `0x204` egérüzenet `[this+0x3b8]==0` esetén a `0x007fda00` módváltót hívja; nem nulla állapotban a `0x007fda80`-at, majd a feltétel sikerén a `0x007fb820`-at és opcionálisan a `[this+0x2e8]` objektum vtable `+0x18` slotját hívja. Ebből a vezérlőn végrehajtott gépi hívásút állítható, de az overlay neve és a felhasználó által látott eredmény nincs bizonyítva.

##### §2 A nyilak a qshow állapotától függnek

Bal/fel esetén a `0x008011b0`, jobb/le esetén a `0x00801210` fut. Mindkettő előbb a `[this+0x3b8]`-at vizsgálja:

| Állapot | Bal/fel | Jobb/le | Közvetlenül bizonyított hatás |
|---|---|---|---|
| `+0x3b8 != 0` | `0x007fd0c0` a `+0x2f8` alobjektum `[+0x30]` mezőjével és `+2.0f` irányargumentummal | `0x007fd0c0` ugyanazzal a mezővel, `-2.0f` irányargumentummal | Az Időrend-ág a két irányt eltérő előjellel adja át; a képernyőn látható irány és képpozíció a teljes `0x007fd0c0` állapot nélkül nem nevezhető meg. |
| `+0x3b8 == 0`, `+0x3bb != 0` | `0x00802980` | `0x008029f0` | Az előző/következő elem hívásútja (38.2.63). |
| `+0x3b8 == 0`, `+0x3bb == 0` | `0x00802ae0` | `0x00802a90` | Mindkettő a `0x008001c0`-t hívja a `+0x46c` pufferrel, majd `+0x518=1`-et és QPC-időt ír `+0x520`-ba. Csak a bal/fel ág csökkenti a `+0x3f4` mezőt kettővel, és negatív eredménynél `-1`-re állítja. A különbség felhasználói jelentése nincs meg. |

##### §3 Bizonyíték, utak és cáfoló kísérlet

| Állítás | Forrás |
|---|---|
| Klienskoordináta skálázása a qshow belső téglalapjára. | bináris (`0x007fde80`, `0x007fdefe`-`0x007fdf5f`) |
| `+0x429` húzás → `0x007fdd00`; felengedéskor `+0x514` → `0x007fd770`; mindkét jelző törlése. | bináris (`0x007fde80`, `0x007fdfaa`-`0x007fdfb2`, `0x007fe1a4`-`0x007fe1cf`) |
| Bal egérgomb `+0x428` ágának `[+0x310]` módosítása. | bináris (`0x007fde80`, `0x007fdf6c`-`0x007fdf9b`) |
| A négy nyílbillentyű-út `+0x3b8`/`+0x3bb` feltételei és célhívásai. | bináris (`0x008011b0`, `0x00801210`) |
| Nem-automatikus bal/fel ág `+0x3f4 -= 2`, ha nulla alá csúszik `-1`; jobb/le ágban nincs közvetlen `+0x3f4` írás. | bináris (`0x00802ae0`, `0x00802a90`) |
| Az overlayek név szerinti azonosítása és húzás közbeni felhasználói látvány. | NINCS MEG |

**A két kódút.** A út: `0x007fde80` eseményágai közvetlenül kezelik a koordinátát, a jelzőket és a `0x007fdd00`/`0x007fd770` hívásokat. B út: a `0x00801270` billentyűkezelő a nyilakat a külön `0x008011b0`/`0x00801210` wrapperekhez irányítja, amelyek eltérő `[+0x3b8]` és `[+0x3bb]` állapotokban külön függvényeket hívnak; a `0x00802ae0`/`0x00802a90` utasításolvasása ellenőrzi a mezőmódosítás különbségét. Ezek a statikus hívás- és mezőállítások egyeznek; a vezérlőnevek és látható hatás **feltételes**, mert élő UI-mérés nem készült.

**Cáfoló kísérlet.** Azt a feltevést próbáltam cáfolni, hogy a nyilak minden állapotban ugyanazt az Időrend-mozgatást végzik. A wrapperek utasításszintű ágai különválasztják a `+0x3b8 != 0` Időrend-ágat a nulla módtól; utóbbiban a `+0x3bb` újabb elágazást ad, és a `+0x3bb==0` bal/fel út `+0x3f4` mezőt módosít. A minden állapotra vonatkozó feltevés cáfolva. A cáfoló ellenőrzés külön elolvasta a két célfüggvényt: `0x00802ae0` írja a `+0x3f4`-et, `0x00802a90` nem. Ez a felhasználói látványt nem azonosítja.

**Bizonyítottsági fok: feltételes.** A mód- és jelzőfüggő gépi híváságakat az utasítások rögzítik; a teljes egérvezérlő név szerinti kötése, az `+0x310` szemantikája, a `+0x3f4` felhasználói hatása és a látható mozgás futásidejű megerősítése hiányzik.

**A #5401 „Kész, ha” állapota.** A 3. pont (vezérlők) részben teljesült: a koordináta-skálázás, az egér húzás/felengedés hívásútja és a mód-/jelzőfüggő nyílágak statikusan le vannak írva. A `timelinedot`, `sliderthumb`, `startbutton`, listaikon, dátumtömb, automatikus léptetés üteme és a teljes felhasználói működés továbbra is nyitott. A 1., 2. és 4. pontot ez a rész nem zárja le.

##### §4 Nyitott

- Mérés szükséges annak megállapításához, hogy a `+0x428`/`+0x429` jelzők és a `[this+0x310]` melyik képernyőelemhez, illetve milyen látható változáshoz tartoznak.
- A `0x007fd770` indexmódosító hatása és a `+0x514` érték jelentése futás közben nincs megmérve.
- A qshow módjelző, a nyílbillentyűk útja és a húzás viselkedésének QEMU-/Wine-ellenőrzése nem készült.

**Új kutatási jegyjavaslat.** Nincs; ezek továbbra is a #5401 vezérlő-elfogadási pontjához tartoznak.

#### 38.2.67 Az első Space-ág aktív objektumcseréje és callbackjei (#5401, 2026-10-22)

**Hatókör.** A 38.2.65-ben nyitva maradt `0x009833a0` host-callback út céljait az eredeti PE vtable-adataival és a callbackek helyi diszasszemblyével ellenőriztem. Ez a kör a statikus objektumcserét zárja le; a látható diavetítést és az Escape utáni folytatási pozíciót nem méri.

##### §1 A qshow és a OneUpUI közti hostcsere

A friss Időrendben a `[this+0x3bb]` nulla (`0x007fda00`, 38.2.9). A `0x00801130` ezt 1-re állítja (`0x00801134`-`0x0080113f`), majd a `0x00802c20`-at hívja (`0x00801157`-`0x00801159`). A `0x00802c20` a negatív `[this+0x3f4]` értéket nullázza, meghívja a `0x00802830`-at, és ha az nulla eredményt ad, valamint a `[this+0x50]` hostmező nem nulla, a `[this+0x2dc]` objektumot adja át a `0x009833a0`-nak gazdaablak-váltásra (`0x00802c20`, `0x00802c2e`-`0x00802c50`). A feltételes `0x00aa6f40` hívás a hostcsere után következik (`0x00801167`-`0x0080116a`).

A `[this+0x2dc]` objektum a `0x00802c60` konstruktor által létrehozott `OneUpUI` (mérete `0x268`, vtable `0x00cbd5c4`); a konstruktora `[OneUpUI+0x25c] = QDrawable` kapcsolatot ír (`0x007fae32`-`0x007fae55`, `0x00802c60`, 38.2.21 §4). A qshow maga a `QDrawable` (`0x00cbd66c`, 38.2.15 §2).

A hostcsere feltétele a `0x00802830` visszatérése. Ez a `[qshow+0x3f0] >> 1` elemszámot ellenőrzi: nulla elemszámnál `4`-et ad; különben a `[qshow+0x3f4]` kijelölt indexet `[0, darab-1]` közé szorítja, az aktuális `[qshow+0x3ec + index*4]` listaelem mutatóját átadja a `0x00802ec0`-nak, majd annak eredményét adja vissza (`0x00802830`, `0x00802831`-`0x00802845`, `0x00802846`-`0x0080286a`, `0x00802954`-`0x0080297b`). A `0x00802ec0` ezt a mutatót az `OneUpUI+0x258` mezőbe írja (`0x00802ec0`, `0x00802ecb`); a OneUpUI felépítésének hibájára `4`, sikerére `0` a visszatérés. Ezért a `0x00802c20` csak nem üres listánál, sikeres OneUpUI-felépítésnél és nem nulla gazdaablak-mutatónál hívja a `0x009833a0`-at. A qshow-listaelem → `OneUpUI+0x258` adatfolyam egy statikus úton **feltételesen** igazolt; hogy a descriptor pontosan milyen képfájlt/puffert jelenít meg, **NINCS MEG**.

A `0x009833a0` a host `[+0x64]` aktív objektumát a kapott mutatóra állítja, a régi és az új objektum vtable `+0x28` slotját hívja, majd `0x00983430`-at futtatja (`0x009833a0`, `0x00983430`). Így a feltételek teljesülésekor az aktív qshow gazdaablak-tartalom a qshow `QDrawable` objektumáról a hozzá tartozó `OneUpUI` objektumra vált.

##### §2 A vtable-callbackek céljai

| Objektum | Vtable slot | Cél a PE-ben | Közvetlen mezőhatás |
|---|---:|---:|---|
| `QDrawable` | `+0x28`, slotcím `0x00cbd694` | `0x007fa480` | A `+0x50` mezőbe írja a kapott szülőablakot; nem nulla szülőnél a `0x00aa67f0`-et is hívja. |
| `OneUpUI` | `+0x28`, slotcím `0x00cbd5ec` | `0x00a6cd00` | A `+0x50` mezőbe írja a kapott szülőablakot. |

A vtable-slot értékeit az eredeti PE nyers bájtjaiból `pefile`-lal olvastam ki, és egyeznek a bináris-index RTTI-adatával (`QDrawable::vftable` `0x00cbd66c`; `OneUpUI::vftable` `0x00cbd5c4`). A két callback diszasszemblye közvetlenül ellenőrzi a fenti mezőírásokat (`0x007fa480`, `0x00a6cd00`). A host `0x00983430` méret-/újrarajzolási útja mindkét vtable `+0x20` slotjának közös `0x00a6cd10` célját éri el; ez a szülő HWND méretét olvassa, majd az objektum `+0x38` slotját hívja. A `OneUpUI` `+0x38` célja `0x00a56800`.

A `0x00801130` ezen az ágon az `ESI`-t a qshow `+0x58` címére állítja, majd a `0x00aa6f40`-et hívja. Ez a függvény a lebegőpontos vezérlőszót elmenti; ha `[qshow+0x2c4]` és `[qshow+0x2bc]` is nem nulla, a `[qshow+0x2c4]` objektum vtable `+0x84` slotját hívja ezekkel az argumentumokkal: `(objektum, 0, qshow+0x2bc, 0, 0x200, 0)`. Negatív visszatéréskor `4`, különben `0` a függvény eredménye; mindkét ág visszaállítja a mentett lebegőpontos vezérlőszót (`0x00aa6f40`, `0x00801130`). A függvény saját törzse nem írja a qshow `+0x3b8`/`+0x3bb` mezőit, de a virtuális cél és a két pointer futásidejű értéke nincs meg.

##### §3 Független utak, cáfoló kísérlet és bizonyítottság

**A út - vezérlési út.** A `0x00801130` állapotírása és hívása, a `0x00802c20` feltételes gazdaablak-váltása, valamint a `0x009833a0` `[host+0x64]` pointerírása megadja az aktív objektum cseréjét. A `0x007fa7f0`/`0x00802c60` konstruktori útja azonosítja a régi `QDrawable` és az új `OneUpUI` objektumot.

**B út - PE-adat és külön callback-olvasat.** Az eredeti PE vtable két nyers `+0x28` bejegyzése `0x007fa480` és `0x00a6cd00`; a hozzájuk tartozó külön diszasszembly a szülőmutató `+0x50` írását mutatja. A `0x009833a0` közvetlen utasításai ugyanazt a két slotot hívják a régi, illetve az új host-objektumon. A két út a callback-célban és az objektumcserében egyezik.

**Cáfoló kísérlet.** Azt a szűk állítást próbáltam cáfolni, hogy a `0x009833a0` callback maga törli a qshow `+0x3b8` vagy `+0x3bb` módmezőjét. A teljes 55 bájtos függvényben a közvetlen írások a host `[+0x3b]` és `[+0x64]` mezőit érik; a két `+0x28` cél a saját objektum `[+0x50]` mezőjét írja. A nyers PE helyértékek és a két callback diszasszemblye ezt külön úton ellenőrzi, ezért a közvetlen mezőtörlési feltevés cáfolva. Ez nem zárja ki a `0x00aa67f0`, a `0x00a56800` vagy a `0x00aa6f40` út esetleges közvetett hatását; ezek felhasználói és állapotbeli hatása továbbra sincs meg.

**Bizonyítottsági fok.** **Megerősített** a feltételes host-objektumcserére és a két `+0x28` callback céljára: a híváslánc, az eredeti PE vtable-adat és a célfüggvények utasításai egyeznek. **Feltételes** a qshow-listaelem `OneUpUI+0x258` mezőbe kötése: egyetlen statikus adatút támasztja alá. A látható „diavetítés” megnevezés és a ténylegesen megjelenő kép **NINCS MEG**; ehhez futó qshow-mérés kell.

**A #5401 „Kész, ha” állapota.** (1) ⛔ A forráshalmaz, sorrend, gyűjteményenkénti darabszám és képlista változatlanul nyitott. (2) ⛔ A teljes képkockánkénti pálya, rétegsorrend és háttérrajz nyitott. (3) ⛔ A Space egyik állapotágának objektumcseréje ismert; a vezérlők, dátumtömb és automatikus lépés teljes működése nyitott. (4) ⛔ A Space sikeres első ága statikusan a `QDrawable` → `OneUpUI` gazdaablak-cseréhez vezet; az élő diavetítés, Escape utáni nézet és folytatási kép/index nincs mérve.

**Nyitott.**

- Ghidra-kör kell: 0x00aa6f40: az `[esi+0x26c]` / `qshow+0x2c4` objektum vtable `+0x84` célfüggvényének osztálya és hatása; a `[qshow+0x2bc]` argumentum forrása; az első Space flag-billentő ágban módosítja-e a qshow `+0x3b8`/`+0x3bb` mezőit [blokkoló]
- Ghidra-kör kell: 0x00a56800: a OneUpUI vtable `+0x38` célfüggvény teljes viselkedése, a belső callbackek és a qshow-állapotra gyakorolt hatás [blokkoló]
- Ghidra-kör kell: 0x00a5e850: a `0x00802ec0` hívási útjában betöltött szerepe; az `+0x3b8` mező, valamint a `0xa5d6b0`/`0xa5db30` hívások hatása, és hogy ezek kapcsolják-e a kiválasztott listaelemet a OneUpUI megjelenítéséhez [blokkoló]
- Élő qshow-mérés kell a tényleges képtartalom, a teljes képernyős diavetítés és az Escape utáni gyűjtemény/kép-index rögzítésére.

**Új kutatási jegyjavaslat.** Nincs; ezek továbbra is a #5401 elfogadási pontjai.

#### 38.2.68 Az `EnumThreadWindows` kilépési callbackje: a `ytWindow` ág kihagyása (#5401, 2026-10-22)

**Hatókör.** A 38.2.64 kilépési útját pontosítja a `0x00983270` és a callback `0x00982fa0` helyi diszasszemblye. A híváságak statikusak; a ténylegesen kiválasztott HWND és az Időrendbe való visszatérés nincs megmérve.

A `0x00983270(this, 0)` először a `[0x00d67858]` értékét vizsgálja. Ha kisebb mint 1, `PostMessageA(this+0x6c, 0x10, 0, 0)`-t hív, majd visszatér. Egyébként `[0x00d6784b]=1` után az aktuális szál ablakain futtatja a `0x00982fa0` callbacket, `lParam=0` értékkel (`0x00983270`, `0x0098328b`-`0x009832c4`; a `0x10` üzenet a WM_CLOSE értéke).

A callback a `GetWindow(hwnd, 4)` eredményét kéri le (`0x00982fa0`, `0x00982fa7`-`0x00982fae`; USER32 IAT `0x00c406f4`). Nulla eredménynél 1-et ad vissza. Nem nulla eredménynél az eredményt a callback `lParam`-jával veti össze; ha az nulla, a célértéket `[0x00d6784c]`-ből veszi. Eltéréskor szintén 1 a visszatérés. Egyezéskor a `GetClassNameA` eredményét a `0x00c7f35c` címen levő `ytWindow` literállal hasonlítja össze: egyezéskor 1-et ad vissza, eltéréskor `SendMessageA(hwnd, 0x10, 0, 0)`-t hív, majd 0-val tér vissza (`0x00982fa0`, `0x00982fc9`-`0x0098307f`; USER32 IAT: `GetClassNameA` `0x00c40800`, `SendMessageA` `0x00c40884`). A kód tehát ezen az enumerációs ágon nem küld közvetlenül WM_CLOSE-t a `ytWindow` nevű osztályú ablaknak. A `[0x00d6784c]` futásidejű értéke és az érintett ablakazonosság **NINCS MEG**.

**Két út és cáfoló kísérlet.** A út: a `0x00982fa0` utasításai megadják a visszatérési ágakat, az összehasonlított literált és az üzenetküldés helyét. B út: a `0x00983270` Ghidra-dekompilátuma külön megerősíti az aktuális szál ablakainak enumerálását, a callback címét és a nulla `lParam`-ot; a PE importtáblája a három USER32 IAT-helyet, a sztringadat pedig a `ytWindow` literált erősíti meg. B részleges ellenőrzés, nem ad önálló második levezetést a callback minden ágára, ezért a teljes callback-viselkedés bizonyítottsági foka **feltételes**.

Cáfoló kísérletként azt vizsgáltam, hogy a callback az egyező `ytWindow` osztályú ablaknak küldi-e a WM_CLOSE-t. A feltételezett ágat a `0x00983031`-`0x0098305b` literál-összehasonlítás és visszatérés cáfolja: az egyezés 1-et ad; az üzenetküldés a `0x00983064`-`0x0098307f` eltérési ágon van. A literál címét és az IAT-célokat a PE adatai külön ellenőrzik. Ez csak a callback ezen útját cáfolja, nem zárja ki, hogy más útvonalon a qshow bezáródjon.

**A #5401 „Kész, ha” állapota.** (1) ⛔ A forráshalmaz, sorrend és képlista nyitott. (2) ⛔ A teljes képkockamozgás és rétegrajzolás nyitott. (3) ⛔ A vezérlők teljes működése nyitott. (4) ⛔ Az egyik `param2=0` kilépési ág statikus callback-viselkedése pontosabb lett; a tényleges bezárás, az Escape utáni nézet és a folytatási kép/index továbbra sincs igazolva.

**Nyitott.** A `[0x00d6784c]` futásidejű értéke, az enumerált ablakok közül ténylegesen érintett HWND, a küszöb alatti `PostMessageA` ág felhasználói hatása, valamint az Időrendből való visszatérés és a folytatási index **NINCS MEG**. A szükséges további bizonyíték a futó qshow sűrű képkocka- és ablakállapot-felvétele; új Ghidra-kör ebből a callbackből nem szükséges.

**Új kutatási jegyjavaslat.** Nincs; a nyitott futásidejű kérdések a #5401 elfogadási pontjai.

#### 38.2.69 A `CThumbUI+0x2c0` objektuma `CAlbumState` (#5401, 2026-10-22)

**Hatókör.** Ez a kör a `CThumbUI+0x2c0` mező típusát azonosítja, és elválasztja a `+0x2bc` `CThumbDB` szolgáltatótól. A CAlbumState mögötti konkrét képhalmazt, annak rendezését és a qshow descriptor-sorozatához való viszonyát nem állapítja meg.

**A út - hívó és argumentum-adatfolyam.** A `0x004051b0` ugyanazt az `ESI` objektumot adja át a `0x00402f90`-nek (`0x004058ee`-`0x004058ef`), majd a `0x004039f0`-nek (`0x0040590d`-`0x0040590e`). A `0x00402f90` a `[X+0x1030]` hiányakor `0x448` bájtot foglal, meghívja a `0x004a1560` konstruktort, és annak eredményét a `[X+0x1030]` mezőbe írja (`0x00402fe2`-`0x00403016`). A `0x004039f0` a `0x005643e0` hívása előtt az `[X+0x1030]` értékét a verembe teszi a `0x00403da4`, `0x00403db4`-`0x00403db8` utasításokkal. A konstruktor `0x005643e0` a második stack-argumentumot a `[this+0x2c0]` mezőbe, a harmadik argumentumot a `[this+0x2c4]` mezőbe írja (`0x005644dd`-`0x005644fa`, `0x0056461c`). Az első argumentumot külön az `EAX`-ből a `[this+0x2bc]` mezőbe teszi (`0x005643f0`, `0x00564616`). A stack-eltolás feloldását a konstruktorban meghívott `0x00a518b0` `ret 4` utasítása (`0x00a51bb2`) ellenőrzi: az előtte betett nulla argumentumot a hívott rutin takarítja le, így a `[esp+0x68]` a `0x004039f0` második argumentumára, azaz `[X+0x1030]`-ra mutat.

**B út - típusazonosítás.** A `0x004a1560` konstruktor a `[this]` mezőbe `0x00c8368c`-t írja (`0x004a1588`). Az eredeti bináris RTTI-/vtable-indexe ezt a címet `CAlbumState::vftable`-ként nevezi meg. Ez az A út pointerláncától független típusbizonyíték: a `CThumbUI+0x2c0` tehát `CAlbumState` objektumra mutat. A `[X+0x1034]` mező külön, a `0x00415790` konstruktorral jön létre, és a `0x00402fdc` címen kerül eltárolásra; a korábbi 38.2.63 szerint ebből lesz a külön `CThumbUI+0x2bc` `CThumbDB` szolgáltató.

A `0x004a0980` a `CThumbUI::MakeTimeline`-ből kapott `CAlbumState` pointerrel fut (`0x005e9434`), és a `[state+0x13c] >> 1` értéket adja vissza (`0x004a09c5`-`0x004a09e9`, illetve `0x004a0a01`-`0x004a0a15`). Ez a MakeTimeline ciklusának számbeli felső határát adja, de önmagában nem nevezi meg az elemeket vagy a mező szemantikáját. A konstruktor `Preferences\datesort`, `Preferences\peoplesort` és `Preferences\albumlistflip` kulcsokat is olvas (`0x004a195f`-`0x004a1a1d`); a binárisban eddig nincs bizonyíték arra, hogy ezek közül melyik, vagy bármelyik, a qshow képeinek sorrendjét állítaná.

**Cáfoló kísérlet.** Azt az egyszerűsítő feltevést próbáltam cáfolni, hogy a `CAlbumState` azonosítása önmagában azt jelenti: a qshow ennek dátum szerint rendezett albumlistáját jeleníti meg. A számlálóút a CAlbumState `+0x13c` mezőjéből ad eredményt (`0x004a0980`); az indexelt elemkérés viszont a `CThumbUI+0x2bc` külön `CThumbDB` objektumának `+0x20` virtuális helyére jut (`0x00562cc0`). A `CThumbDB::vftable` `0x00c81f78` nyers PE-bejegyzésének `+0x20` célja `0x00423300`. Ez a külön számláló- és elemszolgáltató út cáfolja, hogy a két objektum szerepét egyetlen „albumlista” mezőként lehetne leírni; a CAlbumState és a qshow tényleges képsorrendje közti kapcsolatot viszont nem cáfolja és nem is bizonyítja. A vtable-célt a nyers PE-ből, az osztályneveket az index RTTI-táblájából külön ellenőriztem.

**Bizonyíték és bizonyítottsági fok.**

| Állítás | Forrás |
|---|---|
| A `CThumbUI+0x2c0` pointere a hívó `[X+0x1030]` mezőjéből származik. | bináris (`0x004051b0`, `0x00402f90`, `0x004039f0`, `0x005643e0`, `0x00a518b0`) |
| A `[X+0x1030]` objektum `CAlbumState`. | bináris (`0x004a1560`, vtable-írás `0x004a1588`) + RTTI (`0x00c8368c`) |
| A `CThumbUI+0x2bc` mező külön `CThumbDB` szolgáltató; annak vtable `+0x20` célja `0x00423300`. | bináris (`0x00402f90`, `0x00415790`, `0x00562cc0`) + RTTI/PE (`0x00c81f78`) |
| A MakeTimeline számlálóút a `[CAlbumState+0x13c] >> 1` értéket kapja. | bináris (`0x005e9434`, `0x004a0980`) |
| A dátum-/emberrendezési beállítások bizonyítják a qshow képsorrendjét. | NINCS MEG |
| A CAlbumState elemlistája, a qshow descriptor-sorozat és a tényleges képek azonossága. | NINCS MEG |

**A két független út.** A út: ugyanaz a hívóobjektum megy át a `0x00402f90` és a `0x004039f0` útvonalon; `+0x1030` a CAlbumState-konstruktorból származik, és a CThumbUI-konstruktor második argumentumaként a `+0x2c0` mezőbe kerül. B út: a CAlbumState-konstruktor elsődleges vtable-írását (`0x004a1588`) az eredeti bináris RTTI-je `CAlbumState`-ként nevezi meg. A pointerlánc és a típus egyezik; a forráshalmaz és a rendezés nem következik belőlük.

**A #5401 „Kész, ha” pontjai.** (1) ⛔ Részben előrehaladt: a `+0x2c0` osztálya és a számláló mező kifejezése ismert; a forráshalmaz, az upstream sorrend, a konkrét képek és a képszám szemantikája nyitott. (2) ⛔ A teljes képkockánkénti pálya, időgörbe és rajzolási rétegek nyitottak. (3) ⛔ A vezérlők teljes működése és a dátumcsúszka leképezése nyitott. (4) ⛔ A diavetítésbe lépés utáni visszatérési nézet és képpozíció nyitott.

**Nyitott.**

- A `0x004a1560`, `0x00423300` és `0x004b0190` Ghidra-kimenete már megvan. Nyitott a `CAlbumState+0x13c` rekordjainak képi jelentése és a `CThumbDB+0x20` által visszaadott elemek feloldása; a qshow token→`CSlice` útja és a `+0x50c` érték forrása (§1/a) ismert, de a token kategóriája, tényleges fotói és dátumsorrendje nem. A maradék megszerzési útja: a `0x004a66e0`/`0x0045fbe0` feltöltött rekordjai és a `0x00423300` kimenetének fogyasztói közti adatkapcsolat célzott követése, majd az eredmény egyeztetése a qshow `+0x2f8` adatobjektumával.
- A dátumcsúszka, `timelinedot`, `sliderthumb`, automatikus léptetés üteme, teljes animáció és Space/Escape utáni folytatási pozíció továbbra is a #5401 nyitott kérdése.

**Új kutatási jegyjavaslat.** Nincs; a fenti kérdések a #5401 négy elfogadási pontjához tartoznak.

#### 38.2.70 A rétegelt gombok kattintási területe, a hívási út és a CThumbDB következő szintje (#5401, 2026-10-22)

**Hatókör.** A qshow overlay-konstruktorát (`0x007fb210`) az eredeti PE utasításaival vetettem össze a találati kezelő (`0x007fda80`) és a hívott átmenet-segédek helyi diszasszemblyével. A statikus erőforrás→objektummező→híváslánc megvan a négy találati gombnál; a callback felhasználói hatása, a teljes képsorrend és a látható mozgásirány nem következik ebből.

**Overlay és találati út.** A `0x007fda80` csak akkor vizsgálja a négy találati téglalapot, ha `[qshow+0x3b8] != 0`. A bemeneti pont a `0x007fde80` által belső qshow-koordinátává alakított `[+0x420,+0x424]`. A `0x007fda80` összehasonlításai az x-tengelyen `X+0x18 <= x < X+0x18+(X+0x08)`, az y-tengelyen `X+0x1c <= y < X+0x1c+(X+0x0c)` tartományt vizsgálják (például startbutton: `+0x750 <= x < +0x750 + +0x740`, `+0x754 <= y < +0x754 + +0x744`; `0x007fda90`-`0x007fdb06`). Eszerint az overlay objektum-alapjához képest `+0x18` az x-kezdőpont, `+0x1c` az y-kezdőpont, `+0x08` az x-kiterjedés és `+0x0c` az y-kiterjedés. Az alsó szélek benne vannak, a felsők kívül esnek a találaton; ez az x87 összehasonlítási sorrendjéből és az utána következő feltételes ugrásokból adódik.

| Erőforrás (`0x007fb210`) | objektum-alap | találati téglalap | találatkor futó bináris út |
|---|---:|---|---|
| `overlays/startbutton` | `qshow+0x738` | bal `+0x750`, felső `+0x754`, szélesség `+0x740`, magasság `+0x744` | `0x007fb820`, majd ha `[qshow+0x2e8] != 0`, annak vtable `+0x18` slotja; a veremargumentumok `-1`, majd az aktuális `[qshow+0x3ec + qshow+0x3f8*4]` elem, negatív indexnél `0` (`0x007fdb08`-`0x007fdb3d`). |
| `overlays/exit` | `qshow+0x580` | bal `+0x598`, felső `+0x59c`, szélesség `+0x588`, magasság `+0x58c` | `0x007fb820` (`0x007fdbc0`-`0x007fdbc2`). |
| `overlays/right` | `qshow+0x558` | bal `+0x570`, felső `+0x574`, szélesség `+0x560`, magasság `+0x564` | `0x007fd150`; a segéd a `[qshow+0x328]` érték ellentettjét és a bináris `0x00cf3a48` címen levő `2.0f` értéket adja a `0x007fd0c0`-nak (`0x007fdc48`, `0x007fd150`-`0x007fd16e`). |
| `overlays/left` | `qshow+0x530` | bal `+0x548`, felső `+0x54c`, szélesség `+0x538`, magasság `+0x53c` | `0x007fd120`; a segéd a `[qshow+0x328]` értéket és a bináris `0x00cf3a48` címen levő `2.0f` értéket adja a `0x007fd0c0`-nak (`0x007fdcd4`, `0x007fd120`-`0x007fd13c`). |

A `0x007fd0c0` mindkét irányból hívja a `0x009a5210` időfüggvényt, majd a `0x009e6010` tárolófrissítőt. A bal/jobb ág átadott előjele bizonyított; hogy ez a kártyák látható mozgásában melyik képernyőirányt jelenti, **NINCS MEG**. A `startbutton` a `0x007fb820` kilépési útját is meghívja, utána pedig az `[qshow+0x2e8]` érték vtable `+0x18` slotját. A `CThumbUI::MakeTimeline` (`0x005e8a70`) a bemeneti struktúra `+8` mezőjét a `CThumbUI+0x27c` alobjektum címével tölti (`0x005e971b`-`0x005e973d`). A qshow építője ezt a struktúrát adja át a qshow-konstruktornak (`0x008037e0`, `0x008038d2`, `0x0080391e`-`0x00803920`); a konstruktor a `+8` értéket a `[qshow+0x2e8]` mezőbe másolja (`0x007fa7f0`), majd ugyanezt az értéket harmadik paraméterként átadja a `OneUpUI` konstruktorának (`0x00802c60`), amely saját `+0x260` mezőjében tárolja. A `CThumbUI+0x27c` alobjektum osztálya/vtáblája és a vtable `+0x18` célfüggvénye **NINCS MEG**. Ez a statikus adatút önmagában nem bizonyítja, hogy a gomb ugyanazt teszi, mint a szóköz vagy a OneUpUI `auto` parancsa.

A `timeline` (`qshow+0x6c0`) és a `sliderthumb` (`qshow+0x710`) téglalapja az egérkezelőben külön húzási útra jut (`0x007fde80` → `0x007fdd00`, felengedéskor `0x007fd770`; 38.2.63 és 38.2.66). A `0x007fda80` négyes találati listájában nincs `timelinedot` (`qshow+0x6e8`) ág. A `timelinedot` statikus rajzolási képlete a 38.2.78-ban megvan; a kattintási/vezérlőműködése, a listaikon és az ismeretlen `[qshow+0x2e8]` callback eredménye továbbra is **NINCS MEG**.

**A képhalmaz szolgáltatója: további helyi adatút, eredmény nélkül.** A `CThumbDB::vftable` nyers PE `+0x20` slotja `0x00423300` (38.2.69). E függvény `0x0042336c`-`0x00423385` között a saját `+0x48` alobjektumának vtable `+0x2c` slotját hívja. A `0x00415790` konstruktor `0x00415804` utasítása ezt a mezőt `0x00c81fa4`-re állítja; az eredeti PE vtable e címének `+0x2c` slotja `0x004406f0`. A `0x00423300` további útja a `0x00423500`-hoz jut (`0x004236dd`-`0x004236ef`). A `0x00423500` helyi diszasszemblye (632 bájt) megerősíti a `+0x48` alobjektum `+0x2c` virtuális hívását (`0x00423521`-`0x00423538`); az egyik ága meghívja a `0x00423780`-at (`0x004236dd`-`0x004236ef`), és e hívás nulla visszatérésekor a `0x006c9d60` és `0x004115c0` következik (`0x004236fa`-`0x00423715`). A `0x00423780` helyi diszasszemblye indexelt tömbön jár végig (`[arg+4] >> 1`, `0x00423780`-`0x00423862`) és `0x28` bájtos cellákkal növeli a segédpuffert (`0x004238cd`-`0x00423968`). E mezők és rekordok szemantikája, a forráskollekció és a rendezési kulcs **NINCS MEG**. A `0x004406f0` a hívott objektumhoz képest `+0xaa8`-at hozzáad (`0x00440753`), majd az így elért `this+0xb00` listamezőt használja indexeléshez (`0x00440797`-`0x004407b4`), és karakterlánc-feldolgozó segédeket hív (`0x004407dd`-`0x00440817`). Ez nem azonosítja a qshow-ban megjelenített képeket. A CAlbumState számlálóútja (`0x004a0980`) és ez az indexelt CThumbDB-szolgáltató ezért továbbra sem egyesíthető bizonyított képlánccá.

**A két független út.** A út: a `0x007fb210` az overlay erőforrásneveket a qshow mezőeltolásaihoz rendeli. B út: a külön `0x007fda80` találati függvény alsó határként használja az `X+0x18`/`X+0x1c` értéket, ezekhez adja az `X+0x08`/`X+0x0c` kiterjedést, és az így képzett téglalapokhoz közvetlen hívásokat rendeli. A nyers mezőeltolásokat és az eseménycélokat e két út egyezése rögzíti; a respack külön jegyzéke megerősíti a `left`, `right`, `exit`, `timeline`, `timelinedot`, `sliderthumb` és `startbutton` erőforrásneveket, a `0x007fde80` pedig külön húzási útban kezeli a timeline és sliderthumb mezőket. Az overlayek felhasználó által látott következménye, a forráshalmaz és az animációs irány nem következik a két útból.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy az `overlays/startbutton` közvetlenül az `auto`/szóköz út szinonimája. A startbutton hit találatkor `0x007fb820`-at és az `[qshow+0x2e8]` vtable `+0x18` hívását futtatja (`0x007fda80`); a qshow billentyű/Auto ág ezzel szemben a `0x00803110` útvonalon módosítja a `[qshow+0x3bb]` jelzőt (38.2.65-67). A két közvetlen hívási út eltér, ezért a közvetlen azonosság cáfolt. A `[qshow+0x2e8]` callback esetleges közvetett autoplay-hatása nyitott marad. Külön cáfoló körben azt is ellenőriztem, hogy a betöltési operandusok sorrendjéből adódó fordított címkézés (`+0x08/+0x0c` = kezdőkoordináta, `+0x18/+0x1c` = kiterjedés) helyes lehet-e. A friss, vak diszasszemblálási ellenőrzés a `fild`/`fcompp` veremrendet és a feltételes ugrásokat végigkövetve ezt cáfolta: a kód az `X+0x18`/`X+0x1c` alsó határt hasonlítja a koordinátával, majd hozzáadja az `X+0x08`/`X+0x0c` kiterjedést; az eredmény `[alsó, felső)`.

**Bizonyítottsági fok.** **Megerősített** a négy erőforrás mezőeltolása, a félig nyitott találati tartománya és közvetlen hívási útja: az overlay-konstruktor, a találati függvény, a cél-segédek utasításai és a vak, független diszasszemblálási ellenőrzés egyezik; az erőforrásjegyzék külön ellenőrzi a neveket. **Feltételes** a startbutton callback felhasználói jelentése és a bal/jobb átadott előjel képernyőn látható iránya. **Nyitott** a CThumbDB-adat útja, az időrendi képlista, a timelinedot és a listaikon működése.

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A CAlbumState számlálási és CThumbDB indexelt szolgáltatói útja szűkebb lett, de a forráshalmaz, rendezés, képek és darabszámok nyitottak. (2) ⛔ Az előző körök kártyagörbe- és képkocka-transzformációs eredményei részlegesek; a teljes mozgáspálya, időgörbe, háttér és rétegsorrend nyitott. (3) ⛔ A bal/jobb/exit/startbutton statikus hívásai, valamint a slider húzási útja pontosabb; a dátumleképezés, timelinedot, listaikon, callback-hatás és autoplay teljes működése nyitott. (4) ⛔ A Space objektumváltásának statikus ága ismert (38.2.67), de a tényleges diavetítés, kilépés utáni nézet és visszaállított képindex nincs megmérve.

**Nyitott.**

- A `0x00423500`, `0x00423780`, `0x006c9d60`, `0x005e8a70` és `0x008037e0` Ghidra-kimenete már megvan (`2026-10-22-ghidra-sor-247-251.txt`, illetve 2026-10-22, sor 202-209). Az ismert dekompilálások és diszasszemblyek nem adják meg a `0x28` bájtos rekord képi jelentését, a fallback blokk olvasóját, illetve a `CThumbUI+0x27c` callback objektumának vtable-típusát és felhasználói hatását. Ezek **NINCS MEG** kérdések; a következő út a rekordmezők íróinak/fogyasztóinak és a `+0x27c` objektum constructor/vtable írójának címhez kötött vizsgálata, majd célzott futásmérés.
- A `timelinedot`, listaikon, dátumcsúszka-leképezés, teljes képkockánkénti pálya és a futás közbeni képsorrend továbbra is nyitott; utóbbiakhoz a futó qshow mérési felvétele szükséges.

**Új kutatási jegyjavaslat.** Nincs; a nyitott pontok mind a #5401 elfogadási feltételeihez tartoznak.

#### 38.2.71 A `0x00423780` legfeljebb négy tömbelem-lekérése nem azonosítja a qshow képláncát (#5401, 2026-10-22)

**Hatókör.** A `0x00423780` belső indexelését és egy másik hívóját ellenőriztem. Ez a CThumbDB adatút egyik segédrutinja, de a lelet nem nevezi meg a qshow-ban megjelenő képeket, és nem ad dátum szerinti sorrendet.

**A lekérés feltételesen levezetett menete.** A rutin a bemeneti mező `+4` értékét egy bittel jobbra tolja (`0x00423780`-`0x0042378d`). Nulla elemszámnál az `EAX=4` értékkel tér vissza (`0x00423793`-`0x004237a4`); e visszatérési érték szemantikája **NINCS MEG**. Nem nulla elemszámnál a ciklushatár `min(elemszám, 4)` (`0x004237ab`-`0x004237c4`). A ciklus `ebp=0`-ról indul, minden körben a forrástömb `ebp`-edik 32 bites értékét tölti be (`0x0042385a`-`0x0042385f`), ezt adja át a `this+0x4c` alobjektum vtable-jának első slotján (`0x0042384c`-`0x00423862`), majd növeli az indexet (`0x00423a13`-`0x00423a1e`). Tehát legfeljebb az első négy forrástömb-értéket kéri le, növekvő tömbindexben; nem a `0,1,2,3` sorszámokat adja át. A sikeresen összegyűlt belső rekordok bejárása később csökkenő indexű (`0x00423a6b`-`0x00423a79`); ebből a képernyőn látható rétegsorrend nem következik.

**Cáfoló kísérlet.** Azt a feltevést ellenőriztem, hogy a `0x00423780` kizárólag a qshow kártyáinak összeállítója. A másik közvetlen hívó, `0x00653370`, ugyanezt a rutint hívja (`0x006533ef`-`0x006533f7`), majd a `geotagging`, `geothumb`, `%s%d.bmp` és `file:///` útvonalon dolgozik (`0x00653458`, `0x00653486`-`0x00653490`, `0x006534d7`). A kizárólag qshow-specifikus értelmezést ez cáfolja; azt nem cáfolja, hogy a qshow másik hívási útja ugyanezt a segédet használja.

**Bizonyítottsági fok.** **Feltételes** a legfeljebb négy elemre, az átadott tömbértékekre és a fordított belső bejárásra: ezeket az eredeti függvény utasításszintű olvasása támasztja alá, független futásidejű mérés nem. **Feltételes** az általános, nem qshow-kizáró használatra is: a másik hívó utasításai a geotagging fájlútvonalat mutatják, de a függvény teljes futási hatását nem mértem.

**Független utak és korlátjuk.** A út: a `0x00423780` helyi diszasszemblye adja a ciklushatárt, a tömbérték átadását és a későbbi csökkenő indexű bejárást. B út: a külön `0x00653370` hívó utasításai a helyadat-bélyegkép (geothumb) fájlútvonalát mutatják, az index `xrefs`-e pedig ezt a címet a `0x00423500` mellett második közvetlen hívóként tartja nyilván. A két út az általános felhasználásra vonatkozó cáfolatban egyezik; a B út nem igazolja függetlenül a négyes korlátot vagy a qshow-ba kerülő elemeket.

**A #5401 „Kész, ha” pontjai.** (1) ⛔ Csak egy általános lekérő segéd első legfeljebb négy forráselemének indexelése ismert; a forráskollekció, a dátumkulcs, a tényleges qshow-képek és a kollekciónkénti darabszám **NINCS MEG**. (2) ⛔ Ez a rutin nem ad új, qshow-hoz rendelt pályát, időzítést vagy rajzolási réteget; a korábbi 38.2.61-62 részleges eredményei mellett a teljes mozgás nyitott. (3) ⛔ A vezérlők, dátumleképezés és lejátszási ütem teljes működése nyitott. (4) ⛔ A diavetítésből visszatérő nézet és képindex nyitott.

**Nyitott.**

- A `0x00423500`, `0x00423780` és `0x004a1560` Ghidra-kimenete már megvan; a dekompilálás nem azonosította a `0x28` bájtos rekordok képi mezőit vagy a qshow-val való azonosságot. Ezek **NINCS MEG** állítások; a következő út a rekordok íróinak és fogyasztóinak célzott adatfolyam-követése, a qshow token/index forrásával való egyeztetéssel.
- A `0x00423780` nulla elemszámnál visszaadott `4` értékének jelentése **NINCS MEG**.
- A qshow tényleges forráslistájának tartalma/sorrendje, a teljes képkockamozgás, a dátumcsúszka leképezése, a `timelinedot`/listaikon működése és a kilépés utáni képindex továbbra is **NINCS MEG**.

#### 38.2.72 A CThumbDB fallback puffert készít, de nem adja vissza a fallback eredményét (#5401, 2026-10-22)

**Hatókör.** A korábban dekompilált `0x00423500`, `0x00423780` és `0x006c9d60` ágához tartozó, eddig helyben nem ellenőrzött `0x004115c0` hívást vizsgáltam. A Ghidra-kimenet a `2026-10-22-ghidra-sor-247-251.txt` fájlban van; a `0x004115c0` 199 bájtját külön az eredeti PE-ből diszasszembláltam. Ez a kör a fallback adatátadását szűkíti, de nem azonosítja a qshow képeit.

**A fallback adatútja.** A `0x00423500` a `0x00423780` visszatérési értékét `iVar2`-ben tartja. Ha ez nulla, meghívja a `0x006c9d60`-at, majd a `0x004115c0`-at (`0x004236ef`-`0x00423715`). A `0x00423500` a későbbi takarítás után `iVar2`-t adja vissza (`0x00423760`-`0x00423775`); a `0x004115c0` saját visszatérési értékét nem teszi ebbe a változóba. A Ghidra-C ezt az ágat `FUN_006c9d60()` → `FUN_004115c0(...)`, majd `return iVar2` sorrendben mutatja (`2026-10-22-ghidra-sor-247-251.txt`, `0x00423500`). A fallback közvetett mellékhatása és a puffert később olvasója **NINCS MEG**.

A `0x004115c0` az `esi+8` és `esi+0xc` 32 bites értékét összeszorozza; `n` a 32 bites `imul`-eredmény. Nullás eredménynél `4` értékkel tér vissza (`0x004115cd`-`0x004115e1`, `0x0041166e`-`0x00411679`). Nem nulla eredménynél 32 bites regiszteraritmetikával `8 + 4*n` értéket képez, az első két dwordként elmenti a két bemeneti értéket, majd a számított `4*n` hosszban másol az `[esi+0x10]` címről a puffer `+8` címére (`0x004115e7`-`0x00411632`; másoló: `0x00bf2350`, indexnév `_memcpy`). Ezután a puffert és a további argumentumokat a `0x006b75f0`-nek adja át (`0x00411633`-`0x0041164b`); nem nulla helper-visszatéréskor azt adja vissza, egyébként nullát (`0x00411656`-`0x00411684`). A két szorzótényező és a négy bájtos elemméret binárisból olvasható; a mezők képi vagy dátumjelentése **NINCS MEG**.

| Állítás | Forrás |
|---|---|
| A `0x00423500` a `0x00423780` eredményét adja vissza; a nulla ágban a `0x004115c0` hívás külön történik, és annak EAX-értéke nem kerül az `iVar2` helyére. | bináris (`0x00423500`, `0x004236ef`-`0x00423775`) |
| A `0x004115c0` a `+8` és `+0xc` értékből számol, `4*n` bájtot másol a `+0x10` bemeneti címről, majd a puffert átadja a `0x006b75f0`-nek. | bináris (`0x004115c0`, `0x00bf2350`) |
| A `0x006b75f0` méretkorlátja `0x00ffffff`; a függvény a blokkfájl állapotát kezeli, és nem dekódolja a puffer képi vagy időrendi mezőit. | bináris (`0x006b75f0`, Ghidra-kimenet: `2026-10-22-ghidra-sor-261-263.txt`) |
| A `0x006b75f0` által kezelt puffer további olvasója, az adott blokk kulcsának qshow-beli jelentése és a qshow-képlánchoz való kapcsolat. | NINCS MEG |

**Független utak és bizonyítottság.** A út: a `0x00423500` hívóágának Ghidra-C olvasata különválasztja a `0x00423780` eredményét a fallback hívástól. B út: az eredeti PE `0x004115c0` diszasszemblálása megmutatja a puffer létrehozását, a `0x00bf2350` másolást és a `0x006b75f0` hívását. A két út abban egyezik, hogy a fallback közvetlen visszatérési értéke nem a `0x00423500` eredménye; a puffer utóéletét egyik sem mutatja. Az állítás ezért **feltételes**.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a `0x004115c0` visszatérési értéke azonos a `0x00423500` végső visszatérési értékével. A hívó a `0x00423780` eredményét `ESI`-ben tartja (`0x004236ef`-`0x004236f8`), a fallback hívás után pedig a `0x00423769` utasítás az `ESI`-t másolja `EAX`-ba. A 199 bájtos callee-út külön megerősíti, hogy a `0x004115c0`-nak saját `0x006b75f0` eredménye van. Ez cáfolja a közvetlen visszatérésiérték-azonosságot, de nem cáfolja, hogy a helper mellékhatásként cache-t vagy más képi adatot készít; ezt a maradékot ugyanazzal a statikus mércével **NINCS MEG**-ként hagytam.

**A blokkíró besorolása és a cáfoló ellenőrzése.** A `0x006b75f0` Ghidra-kimenete a pufferméret `0x00ffffff` feletti esetét elutasítja, majd a CBlockFile zárolási, blokkindex- és pufferkezelő útján halad; képadatot vagy időrendi rendezési mezőt nem értelmez (`2026-10-22-ghidra-sor-261-263.txt`, `0x006b75f0`). Ettől független ellenőrzésként a Ghidra hívólistáját összevetettem az index `xrefs` táblájával: mindkettő 19 hívási hivatkozást sorol, az egyik önhívással együtt, több különböző hívófüggvényben, köztük `0x0080f830` (filmgyorsítótár), `0x007ead60` (hasonlósági adatbázis) és `0x00425f60` (geo-nézet). A `pmp-database.md` 8.11 és a `picasa-kereses-modok.md` 28. szakasza ugyanezt a címet CBlockFile-íróként, többféle tárolási felhasználással azonosítja.

Cáfoló próbának azt az értelmezést vetettem alá, hogy a `0x006b75f0` maga állítja elő vagy írja le a qshow fénykép-sorrendjét, mert a CThumbDB fallback eléri. A függvény teste csak generikus blokkfájl-adatot kezel, a hívólista pedig több, egymástól eltérő adatfajtát tartalmaz; ez cáfolja a helper qshow-specifikus besorolását. Nem cáfolja, hogy a `0x004115c0` hívása cache-mellékhatást okoz, vagy hogy egy másik út később ezt a blokkot olvassa. A két független út a helper belső adatkezeléséből, illetve a hívók és a korábban dokumentált más felhasználások egyezéséből áll. **Megerősített** csak az, hogy a `0x006b75f0` általános blokkfájl-író; a fallback-puffer qshow-beli szerepe **nyitott**.

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A fallback puffermérete és adatátadása pontosabb; a forráshalmaz, a gyűjtemény, a rendezési kulcs, a képek és a kollekciónkénti elemszám nyitott. (2) ⛔ Ez az ág nem ír le új qshow-mozgást, időzítést vagy rajzréteget; a teljes pálya és rajzolás nyitott. (3) ⛔ A dátumcsúszka, `timelinedot`, listaikon és automatikus léptetés teljes felhasználói működése nyitott. (4) ⛔ A szóköz utáni tényleges nézet, a kilépéskori pozíció és a folytatási képindex nyitott.

**Nyitott.**

- A `0x006b75f0` és `0x004a66e0` Ghidra-kimenete már megvan (`2026-10-22-ghidra-sor-261-263.txt`). A blokkíró általános CBlockFile-író; nyitott a `0x004115c0` által átadott blokk kulcsa, későbbi olvasója és qshow-beli használata. Újabb Ghidra-dekompilálás önmagában ezt nem dönti el.
- A CAlbumState `+0x13c` elemszámának és `+0xc4` providerének forrása, rekordtípusa és rendezése továbbra is nyitott; a `0x004a66e0` kimenete az állapotvektor átméretezését mutatja, de a feltöltő út szemantikáját nem. A kapcsolódó rövid/összetett függvények célzott vizsgálata a 38.2.73-ban szerepel.
- A `0x00423500`, `0x00423780`, `0x006c9d60`, `0x004a1560` már rendelkezik Ghidra-kimenettel; az eddigi dekompiláció az itt felsorolt rekord-, forrás- és sorrendjelentéseket nem dönti el.
- A futó qshow sűrű képkocka-felvétele, az `A` tömb elemeinek jelentése, a `0x006b75f0` pufferfogyasztója és az Escape utáni pozíció **NINCS MEG**.

**Új kutatási jegyjavaslat.** Nincs; a nyitott kérdések a #5401 négy elfogadási pontjához tartoznak.

#### 38.2.73 A CAlbumState albumcsoportjai nem azonosítják a qshow képláncát (#5401, 2026-10-23)

**Hatókör.** A `0x004a66e0` már meglévő Ghidra-kimenetét a `0x0045fbe0`, `0x004a57a0` és `0x004abe70` eredeti PE-ből készült, függvényenkénti diszasszemblyével ellenőriztem. A cél annak szétválasztása, hogy mit árul el a `CAlbumState` felépítése, és mit nem bizonyít a qshow-ban szereplő képekről.

**A CAlbumState feltöltésének határa.** A `0x004a66e0` a `[state+0x13c] >> 1` elemszámot a `0x0045fbe0` visszatérésével egyezteti; eltéréskor `0x24` bájtos rekordok számára foglal/állít át puffert a `[state+0x138]` pointeren, és a hiányzó rekordokat a `0x004ba420` hívásával inicializálja. A rutin a `Preferences\FastStart` értékét is olvassa; a Ghidra-C szerint csak a nulla ágban hívja a `0x004abe70` és `0x004a57a0` feltöltő útvonalakat (`2026-10-22-ghidra-sor-261-263.txt`, `0x004a66e0`). A `0x0045fbe0` a bemeneti objektum `+0xb50` alobjektumának `+0x58` vektorából olvassa a vektor `+0x4c` mezőjét `>> 1` alakban, null vektornál nullát ad (`0x0045fbe0`, `0x0045fbed`-`0x0045fc65`). Ez a számláló adatútja; az elem rekordtípusa és a `0x004a66e0` által kezelt elemszám képi jelentése **NINCS MEG**.

A `0x004abe70` diszasszemblye a `[state+0xc4]` alatti szolgáltatón dolgozik. A `0x004abec3`-`0x004abf31` címeken a `Folders on Disk`, `My Albums`, `Exported Pictures`, `Other Stuff` és `Labels` neveket adja át a `0x985ff0` segédnek; később a `People`, `CAlbumState::HelloCollection`, `Starred Photos`/`CThumbDB::starredphotos`, `Screensaver`, `Recently Updated`/`CThumbDB::RecentUpdate`, `Emailed`/`CThumbDB::Emailed` és `Uploaded`/`CThumbDB::Exported` nevek és kulcsok is szerepelnek (`0x004ac095`, `0x004ac35a`, `0x004ac47e`-`0x004ac589`). Ez bizonyítja, hogy e CAlbumState-felépítő út album- és gyűjteménykategóriákat kezel; nem bizonyítja, hogy mindegyik bekerül a qshow bemeneti listájába, vagy hogy ezek képfájlok.

A `0x004a57a0` a `[state+0xc4]+0xf8` objektum `+0x3f4` elemszámából indul, indexelt rekordok `+0x18`, `+0x1d` és `+0x20` mezői alapján ágakat választ, és egy további szolgáltató `+0x58` vektorát ellenőrzi (`0x004a57c1`-`0x004a57cd`, `0x004a5866`-`0x004a5a8e`). A mezők nem adnak önmagukban dátumkulcsot vagy qshow-descriptor-azonosságot. A mezőfeltételek, forrásobjektum és sorrend **NINCS MEG**.

**Két út és bizonyítottság.** A út: a `0x004a66e0` Ghidra-kimenete azonos `state` paraméterből állítja a `+0x13c` számlálót, és a `FastStart` feltételhez köti a két feltöltő függvény hívását. B út: az eredeti PE `0x004abe70` diszasszemblye közvetlenül mutatja a kategória- és kulcsszövegeket, a `0x0045fbe0` diszasszemblye pedig megmutatja a megszámlált vektormezőt. A két út a CAlbumState albumcsoportokat kezelő szerepével egyezik; az elemek képi tartalmát és qshow-beli részhalmazát egyik sem nevezi meg. **Feltételes** az, hogy ez az általános kategóriaépítés meghatározza a qshow képláncát; **megerősített** csak a hívásfeltétel és a felsorolt kategória-/kulcsnevek binárisbeli jelenléte.

**Cáfoló kísérlet.** Azt a feltevést próbáltam cáfolni, hogy a `CAlbumState` kategóriáinak neve és számlálója közvetlenül megadja a qshow összes képét, darabszámát és sorrendjét. A qshow pointerlánc a `CThumbUI+0x2c0` `CAlbumState` mezőjéből indul (38.2.69), de a `0x008018a0` külön a oneup `+0x2f4` descriptor-bemenetét adja át a generikus `0x004b0190`-nek (38.2.63); a `0x004a66e0` feltöltő ágai ráadásul a `FastStart` értékétől függenek. A közvetlen azonosságot a két külön adatút nem támasztja alá, ezért azt nem fogadom el. Ez nem cáfolja, hogy egyes CAlbumState-kategóriák vagy rekordok a descriptor-szolgáltatóba kerülnek; ezt az összekötést továbbra is meg kell találni.

| Állítás | Forrás |
|---|---|
| A `CAlbumState+0x13c` számlálót a `0x0045fbe0` eredményével egyezteti; a `+0x138` rekordpuffert kezeli, és `FastStart==0` esetén hívja a két feltöltő útvonalat. | bináris (`0x004a66e0`, Ghidra-kimenet: `2026-10-22-ghidra-sor-261-263.txt`) |
| A `0x0045fbe0` a bemenet `+0xb50` alobjektumának `+0x58` vektorában levő `+0x4c >> 1` értéket adja vissza, null vektornál nullát. | bináris (`0x0045fbe0`) |
| A `0x004abe70` album-/gyűjteménykategória-neveket és CThumbDB-kulcsneveket használ. | bináris (`0x004abe70`) |
| A CAlbumState pontos rekordtípusa, a qshow-ban ténylegesen használt kategóriák, képek, dátumkulcs és sorrend. | NINCS MEG |

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A kategóriacsaládok egy része azonosítható, de a qshow képlánca, konkrét képei, sorrendje és elemszámai nyitottak. (2) ⛔ A teljes képkockánkénti mozgás és rétegrajzolás nyitott. (3) ⛔ A `timelinedot`, listaikon, dátumcsúszka szemantikája és tényleges autoplay-periódus nyitott. (4) ⛔ A diavetítés utáni visszatérő nézet és képindex nyitott.

**Nyitott.**

- A `0x004a57a0` és `0x004abe70` Ghidra-kimenete már megvan (`2026-10-23-ghidra-sor-264-267.txt`); az ott látható CAlbumState-kategóriák és rekordfeltételek nem azonosítják a qshow token/index konkrét értékét, a CThumbDB-lista tényleges fotóit vagy dátumsorrendjét. Ezek **NINCS MEG** állítások; megszerzésükhöz a CAlbumState-feltöltő kimenetét kell a `0x004a5710`-en át a qshow `+0x2f4`/`+0x50c` bemenetével és a CThumbDB tokenlistával egyeztetni.

**Új kutatási jegyjavaslat.** Nincs; ezek a #5401 képlánc-elfogadási pontján belüli nyitott kérdések.

#### 38.2.74 A qshow indexelt eleme a CThumbDB tokenoszlopából jön (#5401, 2026-10-23)

**Kérdés.** A qshow `[this+0x50c]` indexe közvetlen képrekordot választ-e, vagy egy CIndexer-keresőszót? A 38.2.63 §1/a a hívási láncot és a lekérdezést már feltárta; ez a kiegészítés az indexelt CThumbDB-mező típusát ellenőrzi.

**A út: a konstruktor és az accessor utasításai.** A `0x00415790` CThumbDB-konstruktor a `0x004158d5` címen a `"token"` literált (`0x00c80d68`) és a rekord `[ebx+5]` mezőjét adja a `0x00985ff0` névépítőnek; a teljes név tartalma ezért a rekordmező nélkül **NINCS MEG**. Az eredményt a `0x004158ee` címen az `L+0xaf0` mezőn inicializálja a `0x004941f0`-nel. Ez a függvény a beágyazott oszlop első vtábláját `0x00c8229c`-re, második vtábláját `+0x48`-on `0x00c822c0`-ra állítja, a nevet `+0x4c`-be, a `+0x58` listamutatót és a `+0x5c` alapértéket nullázza (`0x004941fe`-`0x00494242`). A `0x004406f0` accessor a beágyazott `+0x58` mezőből veszi a vektorobjektumot; annak `+0x48` adatmutatójából és `+0x4c >> 1` elemszámából választ indexelt elemet, határon kívüli indexnél a beágyazott `+0x5c` értéket használja (`0x004407a1`-`0x004407b9`). A kiválasztott elem szövegét a `0x004dca40` CIndexer-keresőnek adja (`0x004408ed`-`0x004408ef`). A qshowban ez az index a `+0x50c` mezőből érkezik (`0x008018a0`, 38.2.63 §1/a). Tehát az indexelt érték keresőszó-sztring; nem közvetlen képrekord-azonosító.

**B út: független RTTI-azonosítás.** A bináris RTTI-index a `0x00c8229c` és `0x00c822c0` címeket egyaránt `CColumn<ytString,0,322043904>::vftable` néven azonosítja. Ez a gépi kódban külön kiolvasott két vtable-írással egyezik, és megerősíti, hogy az `L+0xaf0` beágyazott mező string-oszlop. Az RTTI a `0x00c81fa4` címet `CThumbDB` vtáblaként nevezi; a `+0x2c` slot a `0x004406f0`-ra mutat. Az `album-sorrend.md` 2.1 és 2.4 ugyanennek az accessornak egy másik, album-tokenes hívási útját mutatja. Ezek az utak az oszlop típusával és a token→CIndexer→`CSlice` lekérdezéssel egyeznek, de a qshow futásidejű tokenértékét egyik sem adja meg.

**Cáfoló kísérlet.** Azt a lehetséges olvasatot próbáltam cáfolni, hogy a qshow `+0x50c` közvetlenül a képek egész azonosítóját indexeli. A `0x004406f0` a listából sztringet választ, és azt a `0x004dca40`-nek adja át; a `0x004dca40` a sztringhez tartozó `CSlice` posting listát tölti. Ez cáfolja a közvetlen képrekord-index olvasatot. Nem azonosítja, hogy a tokenlista qshow-beli indexén ténylegesen mely sztring áll, a posting lista mely rekordjai képek, vagy mi a sorrendjük.

| Állítás | Forrás |
|---|---|
| A CThumbDB `L+0xaf0` mezője a `"token"` és `[ebx+5]` mezőből képzett nevű string-oszlop; az accessor az indexelt sztringet adja a CIndexer-nek. | bináris (`0x00415790`, `0x004941f0`, `0x004406f0`, `0x004dca40`) |
| A két beágyazott vtable `CColumn<ytString>` típusa. | bináris RTTI (`0x00c8229c`, `0x00c822c0`) |
| A qshow `+0x50c` futásidejű értéke, a tokenlista feltöltője és sorrendje, a posting lista képrekordjai és száma. | NINCS MEG |

**Bizonyítottság.** **Megerősített** a mezőtípus és az indexelt érték sztringként való átadása, mert a konstruktor/accessor utasításai és az önálló RTTI-azonosítás egyezik. A token tényleges értéke és az általa kiválasztott képlánc **nyitott**.

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A token-oszlop és az index→CIndexer adatút megerősített; a tényleges token, képhalmaz, dátumkulcs, sorrend és darabszám nincs meg. (2) ⛔ A `0x00802230`/`0x007fbab0` korábban dokumentált mozgásképletei nem adják a teljes képkockánkénti pályát és az összes rajzréteget. (3) ⛔ A csúszka képernyő-x→index képlete ismert (38.2.63 §3), de az `A` tömb dátumjelentése, a `timelinedot`/listaikon teljes vezérlése és az autoplay mért periódusa nincs meg. (4) ⛔ A diavetítési ág statikus módváltása megvan, de a futás közbeni látható váltás, Escape utáni nézet és visszatérő képindex nincs mérve.

**Nyitott.** A qshowban kiválasztott token és a CThumbDB tokenlista feltöltő útja **NINCS MEG**; megszerzéséhez a futó qshow `[this+0x50c]` értékét, a `0x004406f0` bemeneti listáját és a visszaadott `CSlice+0x64` elemeit ugyanazon mérési futásban kell rögzíteni, majd az `0x008018a0` kártyaépítésével összevetni. A `0x00419d10` eltolás-találata önmagában nem azonosít qshow-listaírót; a bináris index e függvényhez `]facealbum:%d` és `]expeople:%d` sztring-xrefeket ad, ami önmagában sem bizonyít, sem zár ki további kapcsolatot.

- A két korábban kért törzs elkészült; a dekompilált eredményt és a fennmaradó segédfüggvény-kérdéseket lásd a 38.2.75-ben.

**Új kutatási jegyjavaslat.** Nincs; ez a képlánc-forrás #5401-en belüli nyitott kérdése.

#### 38.2.75 A `+0xaf0` találatok nem azonosítják a qshow tokenlista íróját (#5401, 2026-10-23)

**Hatókör.** A 38.2.74-ben nyitva hagyott `0x00419d10` és `0x00439a80` címeket a `functions` indexből vett mérettel diszasszembláltam (`4877`, illetve `9820` bájt). A korábbi Ghidra-kérés után mindkét függvény törzse megjelent a `2026-10-23-sor-277-280.txt` kimenetben; ezt az eredeti utasításokkal és a hívói kontextussal ellenőriztem. A teljes `.text` streaming vizsgálata korábban a `paszta.memoria_kapu()` hívással indult, és a `+0xaf0`, `+0xb00`, `+0xb04` operandusokra szűrt. Wine nem érhető el ezen a környezeten; futó qshow-mérés nem készült.

**A jelölt függvények közvetlen mezőművelete.** A `0x00419d10` Ghidra-törzse a `param_1+0xaf0` mezőn át a vtable `+0x18`/`+0x1c` helyeit hívja a zárolási útban. A látható rekordműveletek a `param_1+0xb48`, `+0xb4c` és `+0x68` mezőkhöz tartoznak; a függvény `"]facealbum:%d"` és `"]expeople:%d"` kulcsokat épít, majd a `0x004dcf60` rutint is hívja. A `0x00439a80` Ghidra-törzse a `param_1[700]` (`+0xaf0`) mező vtable `+0x18`/`+0x1c` hívásait használja zárolásra. A `"]web_"` és `"]screensaver"` ágak további index-/rekordműveleteket végeznek; a `0x00439960` és `0x004dca40` hívását a diszasszembly is mutatja. A két törzs nem azonosítja a hívó objektumot a qshow CThumbDB-jeként, és nem köti a látható rekordokat a qshow `+0x388` tömbjéhez.

**Független kontroll és hamis pozitív.** A memória-kapuval indított teljes pásztázás a `0x0073fe68` címen szintén talált `+0xaf0` írást: `mov dword ptr [ebx+0xaf0], ecx`. A függvénycím (`0x0073f320`) az RTTI-ben a `CImageOutput::vftable` metódusaként szerepel. Ez függetlenül megmutatja, hogy a puszta `+0xaf0` eltolás nem azonosít qshow- vagy CThumbDB-mezőt. A teljes pásztázásban a `+0xaf0`/`+0xb00`/`+0xb04` minták stack-lokális előfordulásokat is adtak; ezeket nem számoltam objektummező-bizonyítéknak.

**A két független út.** A út: a Ghidra-törzsek megmutatják, hogy a `+0xaf0` mindkét függvényben zárolási vtable-hívás bemenete, miközben külön rekord-/indexmezőkön zajlik a látható munka. B út: az eredeti PE diszasszemblye igazolja a hívási helyeket; a hívói xrefek és a `#tmp`, `]facealbum`, `]expeople`, `]web_`, `]screensaver` sztringek külön adatútból adják a műveleti kontextust, a kapus pásztázás pedig RTTI-vel ellenőrzött `CImageOutput`-találatot ad azonos eltolásra. A két út az eltolás-alapú osztályazonosítás korlátjában egyezik; a segédek közvetett hatására egyik sem ad végleges választ.

**Következtetés és bizonyítottság.** **Feltételes:** a két függvényben nincs közvetlen tárolás az alapobjektum `+0xaf0` mezőjére; a Ghidra-törzs és az utasításszintű olvasat egyezik abban, hogy e mező a zárolási útban szerepel. A `0x00419d10` látható `+0xb48`/`+0xb4c` műveletei és a `0x00439a80` kulcs-/indexágai nem bizonyítják a qshow CThumbDB tokenlistáját. A hívott segédek közvetett módosítása és a hívó objektumok pontos típusa továbbra sincs eldöntve.

**Cáfoló kísérlet.** Azt a jelöltet vizsgáltam, hogy a két függvény a `+0xaf0` egyezés miatt maga a qshow CThumbDB tokenoszlopának írója. A Ghidra-törzsek és a diszasszembly a mezőt zárolási vtable-hívásként mutatja; a látható rekordműveletek más mezőket érintenek. A korábbi ellenpélda szerint ugyanezt az eltolást a `0x0073f320` `CImageOutput` metódusa is írja (`0x0073fe68`), RTTI-azonosítással. Ez cáfolja az eltolásból önmagában levont osztályazonosítást, de nem cáfolja a hívott segédek közvetett hatását.

| Állítás | Forrás |
|---|---|
| A `0x00419d10` és `0x00439a80` a `+0xaf0` mezőt vtable `+0x18`/`+0x1c` zárolási útján használja; ez nem azonosítja a qshow tokenlistáját. | bináris (`0x00419d10`, `0x00439a80`; Ghidra: `2026-10-23-sor-277-280.txt`; diszasszembly) |
| A `0x00419d10` `]facealbum:%d`/`]expeople:%d` ágai a `+0xb48`/`+0xb4c` és `+0x68` mezőkkel dolgoznak. | bináris (`0x00419d10`, `0x004dcf60`; string xrefek) |
| A `0x00439a80` `]web_`/`]screensaver` ágai index-/rekordsegédeket hívnak. | bináris (`0x00439a80`, `0x00439960`, `0x004dca40`) |
| A két jelölt függvényt a `#tmp`-t kezelő `0x0041b580`, illetve a DB-ágakat kezelő `0x0041ba40`/`0x0041ee10` hívja. | bináris xref + diszasszembly (`0x0041b5d9`, `0x0041ba9c`, `0x0041f915`; `#tmp`, `#contacts`, `]screensaver`, `starlist.txt`, `Preferences`) |
| A `+0xaf0` közvetlen írás egy `CImageOutput` metódusban is előfordul. | bináris (`0x0073fe68`, függvény `0x0073f320`) + RTTI (`CImageOutput::vftable`, `0x00cb037c`) |
| A két jelölt függvény közvetett hívásai módosítják-e a qshow `CThumbDB` tokenoszlopát; a qshow `[+0x50c]` tényleges tokenje és a lista futásidejű tartalma. | NINCS MEG |

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A tokenoszlop adatútja tisztult, de a konkrét token, képek, dátumkulcs, sorrend és elemszám nincs meg. (2) ⛔ A teljes képkockánkénti pálya, időzítés és rétegrajzolás nyitott. (3) ⛔ A dátumcsúszka értelmezése, a `timelinedot`/listaikon teljes működése és a tényleges autoplay-periódus nyitott. (4) ⛔ A diavetítés után visszaálló nézet és képindex nyitott.

**Nyitott.**

- Ghidra-kör kell: 0x004dcf60: a `0x00419d10` által a `+0x68` alobjektumon hívott rutin milyen adatot olvas vagy módosít, és kapcsolatban áll-e a qshow CThumbDB tokenoszlopával? [blokkoló]
- Ghidra-kör kell: 0x00439960: a `0x00439a80` `]screensaver`/`]web_` útján hívott segédje csak az indexelőben keres, vagy a qshow CThumbDB tokenlistáját is módosítja? A meglévő `0x004dca40` kimenet a kereső segédet mutatja, de ezt a hívó segédet nem. [blokkoló]
- A qshow aktuális `[this+0x50c]` értéke, a tokenlista teljes sorrendje és a `CSlice+0x64` képrekordjai: **NINCS MEG**. Megszerzésükhöz ugyanazon futó qshow-mérésben kell rögzíteni e mezőket; ehhez Wine-futtatókörnyezet szükséges, ami itt nem áll rendelkezésre.

**Új kutatási jegyjavaslat.** Nincs; ez továbbra is a #5401 képlánc-elfogadási pontja.

#### 38.2.76 Az egérfelengedés animációs rekordot ütemez (#5401, 2026-10-23)

**Hatókör.** A 38.2.63-ban dokumentált csúszka-felengedési hívást (`0x007fde80` → `0x007fd770`) összevetettem az animátor kiértékelőjével és rekord-hozzáfűzőjével (`0x009e5e70`, `0x009e6010`). A `0x007fd770` Ghidra-kimenete már megvan (`2026-10-21-idorend-21.txt`); a kis segédek utasításait az eredeti PE-ből ellenőriztem. A qshow élő képernyőjét vagy ezt a teljes hívási láncot QEMU-ban nem futtattam.

**A felengedési út.** Ha az egérkezelő húzásjelzője aktív, a `WM_LBUTTONUP` ág a `[this+0x514]` indexet a `0x007fd770`-nek adja át (`0x007fde80`, `0x007fe1a4`-`0x007fe1cf`). A `0x007fd770` a P animátor aktuális vagy utolsó végpontját olvassa, lekéri a QPC-alapú másodpercet (`0x009a5210`), majd a `P+0x38` interpolátort kiértékeli (`0x009e5e70`). Ezután az indexet és a P `+8`, `+0x20`, `+0x30` mezőit használó eltolást ad át a `0x007fd0c0`-nak. Az útvonal a kiválasztott indexet időbeli pozícióvá alakítja, de nem azonosítja az indexhez tartozó konkrét képet vagy dátumot; a `P+0x30` kártyaköz szerepe és írójának hiánya a 38.2.24 §1-ben van rögzítve.

A `0x007fd770` második argumentuma a PE `0x00c7e4a4` címén levő `0x40800000` f32 konstans, azaz pontosan `4.0`. A `0x007fd0c0` az aktuális QPC-másodpercet (`0x009a5210`) és ezt az időtartamot teszi az új, 0x28 bájtos animátorrekord kezdő- és végidejévé, majd a `0x009e6010`-on át a rekordlistához fűzi. A rekord kiértékelésénél a `0x009e5e70` az időintervallumra normalizált értéket a rekord `0x0072df60` easing-függvényének adja át; ennek görbéjét és QEMU-pontjait a `picasa-idorend-viselkedes.md` 38.2.24 §1 és 38.2.32 már rögzíti. A binárisbeli 4,0 másodperc a belső animátorrekord időtartama; önmagában nem bizonyítja a felhasználó által látott kép vagy dátum mozgását.

**A két független út.** A út: az egér-felengedés diszasszemblálása az indexet a `0x007fd770`-nek adja; a függvény a `0x007fd0c0`-t hívja a `0x00c7e4a4` konstanssal. B út: a bal/jobb vezérlők (`0x007fd120`, `0x007fd150`) és a qshow nyílágai (`0x00801270` → `0x008011b0`/`0x00801210`) ugyanezt a `0x007fd0c0` rekordkészítőt hívják, ott `2.0` másodperces időtartammal; a 38.2.24 §1 ezt és a rekord `kezdőérték/végérték/kezdőidő/végidő` mezőit külön rögzíti. A két út egyezik abban, hogy a felengedés a közös időalapú animátorba ütemezett frissítést ad, de a 4,0 másodperces paraméter csak az egérút sajátja.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a csúszka felengedése közvetlenül beállítja a kiválasztott képet vagy az animátor kurzorát. A teljes `0x007fd770` utasítássor az aktuális állapot és interpoláció kiolvasása után `0x007fd0c0`-t hívja; az utóbbi új rekordot épít, a `0x009e6010` pedig a rekordot a tömbhöz fűzi. Közvetlen képindex-írás nem látható ezen az útvonalon, így a „közvetlen ugrás” feltevés megbukik. Ez nem bizonyítja a qshow képernyőn látható mozgás irányát, dátumjelentését vagy végállapotát.

| Állítás | Forrás |
|---|---|
| Egérfelengedéskor a `[this+0x514]` index a `0x007fd770`-hez kerül. | bináris (`0x007fde80`, `0x007fe1a4`-`0x007fe1cf`) |
| A `0x007fd770` a QPC-időt és a `P+0x38` interpolációját olvassa, majd a `0x007fd0c0` frissítőn át folytatja. | bináris (`0x007fd770`, `0x009a5210`, `0x009e5e70`, `0x007fd0c0`) |
| Az egérút az animátorrekordot 4,0 másodperces belső időtartammal készíti; az `0x009e6010` a rekordot a tömbhöz fűzi. | bináris (`0x00c7e4a4` = f32 4,0; `0x007fd0c0`, `0x009e6010`); QPC-másodperc: `0x009a5210` |
| A felengedés által kiválasztott indexhez tartozó konkrét dátum, kép és látható mozgás/végállapot. | NINCS MEG |
| A teljes egér-felengedési híváslánc QEMU-eredménye és sűrű qshow-képkocka-felvétele. | NINCS MEG |

**Bizonyítottsági fok.** **Megerősített** a belső híváslánc és a rekord 4,0 másodperces időtartama: a csúszkaág, a közös rekordkészítő és az ettől független nyílvezérlő út egyezik; az időalapot a QPC-frekvenciával osztó `0x009a5210` adja. **Feltételes** a felhasználói „animált keresés” megfogalmazás, mert a képernyőn látható eredmény nincs rögzítve.

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A kiválasztott index/animátor kapcsolat pontosabb, de a dátumtömb, a képek és forráskollekciók nincsenek meg. (2) ⛔ A rekord időzítése és easing-függvénye ismert, a teljes képkockánkénti kártyapálya és rétegrajzolás nyitott. (3) ⛔ A húzás felengedésének 4,0 másodperces belső rekordja igazolt; a dátummező jelentése, `timelinedot`, listaikon és tényleges autoplay-ütem nyitott. (4) ⛔ A diavetítésből visszatérő nézet és képindexe nincs meg.

**Nyitott.** A `[this+0x514]`-hez kiválasztott indexből előálló dátum és képtartalom; az `A` tömb és a P `+8`, `+0x20`, `+0x30` mezők forrás-/időjelentése; a célzott animátorérték képkockánkénti képernyőhatása. Ezekhez a qshow adatait és sűrű képkockáit ugyanazon Wine-futásban kell rögzíteni. Új Ghidra-kör ehhez a `0x007fd770` hívási lánchoz nem szükséges.

#### 38.2.77 A csúszka index- és hüvelykujj-leképezésének QEMU-kontrollja (#5401, 2026-10-23)

**Hatókör és mérési állapot.** A `0x007fdd00` eredeti gépi kódját `qemu-i386` alatt futtattam. A qshow-objektumot és a tömböket kézzel állítottam be: alsó x-határ `100`, szélesség `400`, `A=[0; 0,25; 0,5; 1]` (f64), négy `0xf8` bájtos rekordmutató (`0x20000000`-`0x20000003`), hüvelykujjszélesség `24`, y `27`. Ez kontrollált függvénypróba, nem futó qshow vagy valódi dátum-/képhalmaz mérése. Az ELF és assembler ideiglenes fájljai a munkafa `.bt/` könyvtárába kerültek.

**A út-bináris.** A `0x007fdd00` az egér x értékét az alsó határ és az alsó határ plusz sávszélesség közé korlátozza, majd a sávon belüli normalizált arányt hasonlítja az `A[i]/A[n-1]` értékekhez. A legkisebb abszolút eltérésű indexet a `[this+0x514]` mezőbe írja; egyező eltérésnél a szigorú `<` összehasonlítás miatt a korábbi index marad. A rekordmutató a `[this+0x3a8]+i*0xf8` címből jön, a listahosszt a `[this+0x3ac]>>1` adja. A hüvelykujj x-pozícióját a sávon belüli egérarányból, a `[this+0x718]` hüvelykujjszélességből és a `[this+0x6d8]` kezdőpontból állítja elő; y-t a `[this+0x72c]` értékére teszi vissza. A pontos mezőút és összehasonlítás az eredeti utasításokban látható (`0x007fdd00`-`0x007fde73`).

**B út-eredeti gépi kód QEMU-ban.** Az alábbi értékeket a qshow-objektumból olvastam ki minden hívás után; a thumb-koordináták egész kimenetek.

| x bemenet | kiválasztott index | rekordmutató | hüvelykujj x | forrás |
|---:|---:|---:|---:|---|
| 50 | 0 | `0x20000000` | 85 | mérés (`qemu-i386`, `0x007fdd00`) |
| 100 | 0 | `0x20000000` | 85 | mérés (`qemu-i386`, `0x007fdd00`) |
| 150 | 0 | `0x20000000` | 135 | mérés (`qemu-i386`, `0x007fdd00`) |
| 200 | 1 | `0x20000001` | 185 | mérés (`qemu-i386`, `0x007fdd00`) |
| 300 | 2 | `0x20000002` | 285 | mérés (`qemu-i386`, `0x007fdd00`) |
| 400 | 2 | `0x20000002` | 385 | mérés (`qemu-i386`, `0x007fdd00`) |
| 500 | 3 | `0x20000003` | 485 | mérés (`qemu-i386`, `0x007fdd00`) |
| 550 | 3 | `0x20000003` | 485 | mérés (`qemu-i386`, `0x007fdd00`) |

A megadott tesztállapotban a thumb-kimenet `100 + t*400 - 15`, ahol `t` a korlátozott x sávon belüli aránya; a 15 a 24 széles teszt-thumb fél szélessége és a binárisban hozzáadott 3 egység összege. Ez csak a megadott bemenetek mérési leírása, nem dátumképlet.

**A két független út.** Az A út a diszasszemblálásból vezeti le a határkorlátozást, az arányok szerinti legközelebbi indexválasztást és a szigorú összehasonlítást. A B út ugyanezeket az eredeti PE-kód futtatásával, beállított qshow-mezőkkel méri; a széleken azonos kimenet, köztes pontokon a várt index és thumb-koordináta jelenik meg. A két út a kontrollált állapotra egyezik.

**Cáfoló kísérlet.** Megpróbáltam cáfolni azt az olvasatot, hogy döntetlen távolságnál az első index marad. Az `x=150` a `0` és `0,25`, az `x=400` a `0,5` és `1` közötti felező. Ha az összehasonlítás a későbbi jelöltet is elfogadná, ezeknél az index `1`, illetve `3` lenne; az eredeti függvény QEMU-kimenete `0`, illetve `2`. A próba ezért nem cáfolta a binárisból olvasott szigorú `<` szabályt. Ugyanebben a futásban az `x=50`/`100` és az `x=500`/`550` párok az alsó, illetve felső határ korlátozását is kontrollálták.

**Bizonyítottsági fok.** **Megerősített** a `0x007fdd00` indexválasztása, határkorlátozása és hüvelykujj-kimenete a fenti kézzel épített tesztállapotra: az utasításszintű levezetés és az eredeti gépi kód QEMU-eredménye egyezik, a döntetlen- és határpróbákkal. **NINCS MEG** az `A` tömb valódi qshow-forrása és jelentése, ezért nem állítható, hogy a kiválasztott index dátumot, Unix-időt vagy egy adott képet jelöl; a felhasználói felületen látható húzás- és végállapotot ez a próba nem mutatja.

| Állítás | Forrás |
|---|---|
| A csúszka indexválasztása, határkorlátozása és thumb-pozíciószámítása a `0x007fdd00` függvényben. | bináris (`0x007fdd00`-`0x007fde73`) |
| A nyolc bemeneti x koordinátához tartozó index, rekordmutató és thumb-x. | mérés (`qemu-i386`, eredeti `Picasa3.exe`, `0x007fdd00`, kézzel épített qshow-állapot) |
| Az `A` tömb valódi előállítója, mezőjelentése, dátum-/képtartalma. | NINCS MEG |
| A csúszka valós qshow-futásban látható animációja és dátumra vetített értéke. | NINCS MEG |

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A csúszka által választott tömbindex futtatásos kontrollja nem azonosítja a képhalmaz forrását, dátumkulcsát vagy sorrendjét. (2) ⛔ Ez a mérés nem egészíti ki a képkockánkénti pályát vagy a rétegrajzolást. (3) ⛔ A csúszka x→index és thumb-x leképezése kontrollált állapotra QEMU-val igazolt; az `A` dátumjelentése, a `timelinedot` kattintási/vezérlőműködése (statikus pozícióképlete: 38.2.78), a listaikon és a valós autoplay-periódus továbbra is nyitott. (4) ⛔ A diavetítésbe váltás és a visszatérő nézet/képindex továbbra sincs futás közben mérve.

**Nyitott.** Az `A` tömb valódi írója, értelmezése, teljes elemlistája és a hozzá kötött képek; a valós qshow húzás közbeni és felengedés utáni képernyőállapota. A valódi állapot és képkockák rögzítéséhez célzott Wine-futás kell; a helyi környezetben Wine nincs. A `0x00419d10` és `0x00439a80` törzse elkészült; a nyitott segédfüggvény-kérdéseket a 38.2.75 sorolja.

#### 38.2.78 A `timelinedot` statikus kirajzolási képlete és duplikált arányai (#5401, 2026-10-23)

**Hatókör.** A `timelinedot` erőforrás qshow-mezőhöz kötését (`0x007fb210`), a qshow rajzoló rutinját (`0x007ffc90`) és a közvetlen egér-találati függvényt (`0x007fda80`) ellenőriztem. A rajzoló eredeti gépi kódját QEMU alatt, kézzel beállított `qshow` mezőkkel és `A` tömbökkel is lefuttattam. Ez a mérés a koordinátaszámítást ellenőrzi; nem valódi qshow-futás, nem valódi dátumtömb, és nem képernyőkép.

**Erőforrás és tömb.** A `0x007fb210` `0x007fb390` utasítása az `EDI` regisztert a `qshow+0x6e8` címre állítja; a `0x007fb397` az `overlays/timelinedot` sztring címét tölti be, a `0x007fb39c` pedig meghívja a betöltőt. A `string_xrefs.csv` külön bejegyzése ugyanezt a sztringet a `0x007fb210`-hez köti. A `0x007ffc90` a `qshow+0x388` című double-tömböt olvassa; az elemek száma `n=([qshow+0x38c] >> 1)`, és a ciklus `n>0` esetén fut. Minden `i` indexhez `r_i=A[i]/A[n-1]` arányt számol. A kezdő összehasonlító érték a bináris `0x00cf3f58` címén levő `-1.0` double. A kód a szomszédos, pontosan egyenlő double arányokat számlálja.

**Koordináták és rajzolási feltétel.** Az eredeti utasításokból (`0x007ffd13`-`0x007ffd2e`, `0x007ffdc6`-`0x007ffe4a`) a mezőszintű képletek:

```text
x_i = 0x00c29990( r_i * float32(uint32([qshow+0x6c8] - 4))
                 + [qshow+0x6d8] - ([qshow+0x6f0] >>arith 1) )
y_i = (([qshow+0x6cc] + 2*[qshow+0x6dc]) >>arith 1)
      - ([qshow+0x6f4] >>arith 1) - vertical_offset
```

`[qshow+0x6c8]-4` után 32 bites dword-kivonás történik; negatív előjelnél a bináris `0x00cf39e4` címen levő `2^32` f32 konstans hozzáadódik, majd az érték f32-ként kerül az x87 szorzásba (`0x007ffd13`-`0x007ffd35`). A `0x00c29990` végzi az x87 lebegőpontos érték egész koordinátává alakítását. Ha `[0xda1428] != 0`, a gyors ág a `cvttsd2si` utasítást használja; egyébként a `0x00c299c6` x87 ága `fistp` után előjel-/tört-rész korrekciót végez (`0x00c299c6`-`0x00c29a3a`). A négy kontrollált FPU control word mindegyikén a két eredeti ág is ugyanazt a nullához csonkolt értéket adta a 38.2.78 QEMU-mérés tesztértékeire; ez helyesbíti a régebbi, 38.2.19-ben szereplő állítást, miszerint a lassú ág csak csonkoló FPU-mód mellett csonkol. A tényleges qshow-futás `[0xda1428]` értéke **NINCS MEG**. A függvény `[qshow+0x700]`-ba írja az x-et, `[qshow+0x704]`-ba az y-t, majd a `qshow+0x6e8` rajzolót adja át a `0x009ab690`-nek. A pontosan egyenlő szomszédos arányoknál a számláló 0, 1 és 3 esetén a függvény rendre 0, 7 és 14 értékű `vertical_offset`-tel rajzol; 2 és minden más számlálóértéknél a rajzolási ág kimarad, a koordináta-mezőket nem írja felül. Ezt a `0x007ffdf2`-`0x007ffe0c` elágazás és a `0x007ffe14`-`0x007ffe4a` író/rajzoló útja adja. A képlet önmagában nem mondja meg, hogy az `A` értékek dátumot vagy más időrendi adatot jelentenek.

**QEMU-kontroll.** Az eredeti `0x007ffc90` futott `qemu-i386` alatt (`timeout 60`, `RLIMIT_AS=(2400+4096) MiB`, core dump tiltva). A kézzel felépített tesztobjektum mezői: `+0x6c8=104`, `+0x6cc=40`, `+0x6d8=200`, `+0x6dc=5`, `+0x6f0=10`, `+0x6f4=10`; a QEMU-környezetben `0x00da1424=1`, `0x00da1428=1` és FPU control word `0x027f` volt beállítva. A környező dekorációs/háttér- és drawable hívások stubjai az eredeti visszatérési stack-takarítást tartották: `0x007fe7c0` `ret 4` (`0x007fee6b`), `0x007fee70` `ret 0x0c` (`0x007ffc7f`), `0x007fd180` `ret 0x0c` (`0x007fd36f`), `0x007fe540` `ret 0x0c` (`0x007fe5e9`/`0x007fe5f8`; a teszt stubja `EAX=1`-et adott), `0x009ab690` `ret 0x1c` (`0x009ab923`). A `0x00c29990` koordináta-átalakító eredeti kódja futott. A tömbök double elemei és kimenetei:

| `A` bemenet | x | y | forrás |
|---|---:|---:|---|
| `[0.125, 0.5]` | 295 | 20 | mérés (`qemu-i386`, eredeti `0x007ffc90`) |
| `[0.125, 0.5, 0.5]` | 295 | 13 | mérés (`qemu-i386`, eredeti `0x007ffc90`) |
| `[0.125, 0.5, 0.5, 0.5]` | 295 | 13 | mérés (`qemu-i386`, eredeti `0x007ffc90`) |
| `[0.125, 0.5, 0.5, 0.5, 0.5]` | 295 | 6 | mérés (`qemu-i386`, eredeti `0x007ffc90`) |

A tesztállapotban a végső `r_i=1`, így az x-kimenet 295; a függvény y-alapja 20. A további y-eltolásokat a mért 13 és 6 kimenet rendre 7 és 14 pixeles eltolásként mutatja. Ez a mesterséges tömbre és mezőállapotra vonatkozó ellenőrzés; a valódi `A` tömb, a pontok (dot) dátumjelentése, a pixelrajz és a teljes animáció továbbra is **NINCS MEG**.

**A `0x00c29990` két ágának külön QEMU-kontrollja.** Az eredeti konvertert `[0xda1428]=1` (gyors ág) és `0` (x87 ág) mellett futtattam, négy FPU control worddal: `0x027f`, `0x067f`, `0x0a7f`, `0x0e7f`. Mind a nyolc kombináció erre a f64 bemenetsorra ezt adta: `[1.25, 1.5, 1.75, 2.5, 2.75, -1.25, -1.5, -1.75, -2.5, -2.75]` → `[1, 1, 1, 2, 2, -1, -1, -1, -2, -2]`. A lassú ág ellenőrzéséhez ugyanabban a QEMU-környezetben nyers `fistp` kontroll is futott `±1.5`-re: a `0x027f` módban `(2,-2)`, `0x067f`-ben `(1,-2)`, `0x0a7f`-ben `(2,-1)`, `0x0e7f`-ben `(1,-1)` lett; a helper mind a négyben `(1,-1)`-et adott. Így a slow-path helper `fistp` kerekítési eredményét korrigálja, nem örökli közvetlenül annak irányát.

| Állítás | Forrás |
|---|---|
| `overlays/timelinedot` → `qshow+0x6e8`. | bináris (`0x007fb210`, `0x007fb390`-`0x007fb39c`); független sztring-xref: `string_xrefs.csv`, `0x00cbd3a0` |
| A normalizált `A[i]/A[n-1]` arány, a pontos ismétlődésszámláló, a mezőalapú x/y képletek és a 0/7/14 ágak. | bináris (`0x007ffc90`, különösen `0x007ffd13`-`0x007ffe4a`; konstansok `0x00cf3f58=-1.0`, `0x00cf39e4=2^32`; konverzió `0x00c29990`) |
| A négy felsorolt koordinátakimenet a kézzel beállított tesztállapotra. | mérés (`qemu-i386`, eredeti `0x007ffc90`, a fenti helyettesítő-korláttal) |
| A `0x00c29990` gyors/lassú ágának eredményei a megadott f64 értékeken és FPU control wordokon; a nyers `fistp` kontroll. | mérés (`qemu-i386`, eredeti `0x00c29990`) |
| A valódi `A` tömb tartalma/jelentése, a ponthoz rendelt képek/dátumok és a képernyőn látható pixelrajz. | NINCS MEG |

**A két független út.** A út: az eredeti PE gépi kódjának utasításszintű olvasata adja a mezőket, az arányszámítást, a számlálóágakat és a rajzolóhívás helyét. B út: az eredeti `0x007ffc90` QEMU-futtatása az ismert, kézzel felépített bemenetekre az x/y koordinátákat közvetlenül a qshow-objektumból adta vissza. A két út a kontrollált állapotra egyezik; a B út nem igazolja a valódi adatforrás vagy a látható qshow-kép jelentését.

**Cáfoló kísérlet.** Azt a feltevést próbáltam cáfolni, hogy a harmadik, azonos normalizált arányú pont 14 pixellel a csoport első pontja alá kerül. A `[0.125, 0.5, 0.5, 0.5]` QEMU-bemenet utolsó `y`-kimenete 13 maradt, nem 6; az objektum kezdőértékét `0x77777777`-re állítottam, ezért ez nem előző futásból maradt érték. A gépi kód a duplikált arányszámláló 2-es esetén a `0x007ffe07`-`0x007ffe51` ágon kihagyja a mezőírást és a rajzolóhívást. A cáfoló eredmény ugyanazzal a mércével ellenőrizve egyezik a kódággal: 14 pixeles eltolás csak a számláló 3-as ágában jelenik meg. Ez nem zárja ki a `timelinedot` más esemény- vagy vezérlési útját.

**A közvetlen kattintási feltevés cáfoló ellenőrzése.** Azt is ellenőriztem, hogy a `timelinedot` közvetlen kattintási cél-e a qshow találatkezelőjében. A `0x007fda80` teljes függvény négy overlay-alapot vizsgál (`qshow+0x738`, `+0x580`, `+0x558`, `+0x530`); a `qshow+0x6e8` nincs közöttük. Az egérkezelő két üzenetágában (`[MSG+4] == 0x203` vagy `0x204`, `0x007fde80`, `0x007fe13c`-`0x007fe15f`) ezt a találatkezelőt hívja. A közvetlen kattintási cél feltevése ezen a hit-test útvonalon cáfolt; más egéresemény, hover vagy közvetett callback nincs kizárva.

**Bizonyítottsági fok.** **Megerősített** a `qshow+0x6e8` mezőbe kötés és a koordinátaszámítás a fenti kontrollált bemeneteken: a gépi kód és az eredeti kód QEMU-kimenete egyezik, az ismétlési próbával. **Feltételes** a képlet felhasználói értelmezése; a valódi tömb tartalma, dátumkapcsolata és képernyőn látható viselkedése nincs mérve.

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A dot koordinátaképlete részben megvan; az `A` tömbből nem derül ki a képek forráskollekciója, dátumkulcsa, sorrendje vagy elemszáma. (2) ⛔ A dot statikus pozíció- és duplikációs szabálya ismert, de a teljes képkockapálya, időgörbe, háttér, kártya és rétegsorrend nincs kész. (3) ⛔ A közvetlen timelinedot-kattintás ezen a hit-test úton kizárt; a listaikon, az `A` valódi szemantikája, az autoplay valós üteme és a vezérlőhatások nyitottak. (4) ⛔ A tényleges diavetítés és az Időrendbe visszatérő képindex/nézet továbbra sincs futás közben mérve.

**Nyitott.**

- A `0x00419d10` és `0x00439a80` dekompilált törzse, illetve a fennmaradó segédfüggvény-kérdések: lásd 38.2.75.
- A `qshow+0x388` tömb valódi előállítója és értelmezése, a tokenhez tartozó képek/dátumok, a listaikon működése, a teljes rajzolási/animációs felvétel, az autoplay üteme, valamint a Space utáni visszatérés helye és indexe: **NINCS MEG**. A felvételhez Wine-futtatás és ugyanazon qshow-állapot képernyőképe és memóriakivonata kell; Wine ezen a gépen nem érhető el.

**Új kutatási jegyjavaslat.** Nincs; ezek a #5401 nyitott elfogadási pontjai.

#### 38.2.79 A `0x007fc010` nem azonosítja az `A` tömb íróját (#5401, 2026-10-23)

**Hatókör.** A 38.2.77-78-ban olvasott qshow `+0x388` `A` tömb lehetséges előállítóját kerestem. A már meglévő Ghidra-kimenetek (`2026-10-21-idorend-7.txt`, `2026-10-21-idorend-25.txt`) mellett a `0x00801cb0`, `0x007fc010`, `0x007ffc90` és `0x007fdd00` eredeti utasításait ellenőriztem. A strukturált offszet-ellenőrzés a `paszta.utasitasok()` függvényt használta, első műveletként `paszta.memoria_kapu()` hívással; a teljes `.text` vizsgálat mért csúcs-RSS-e 95,7 MiB volt. A külső `systemd-run` korlátot a helyi user bus nem engedte beállítani. A qshow valódi futását vagy a függvény qemu-i386 futtatását ebben a körben nem mértem.

**A kártyarajzolási út.** A `0x00801cb0` hívó a `0x007fc010`-nek a qshow `+0x2f8` címét adja első, a `+0x2c8` címét második paraméterként (`0x00801cb3`-`0x00801cc1`). A `0x007fc010` az első paraméter `+0xb4` mezőjéből veszi a ciklusszámot, `>>1` után; a hívás címzésével ez a qshow `+0x3ac` mező. A ciklus minden rekordhoz meghívja a `0x007fbab0`-t, az eredmény három 32 bites lebegőpontos elemét olvassa (`0x007fc100`-`0x007fc123`), majd a harmadik értéket egy lokális `float` sorozatba teszi. A qshow `+0x378` címen levő vektormező a sorozathoz tartozó rekordindexeket tartja; a ciklus a 0xf8 bájtos képrekordokon transzformációs adatokat állít elő, és ezeket a `0x007fa650`-nek adja át. A végén a `0x00604480` segédet hívja; az index `xrefs` táblában ennek hat különböző hívó függvénye van, ezért maga a segédfüggvény nem timeline-specifikus azonosító.

Ez az út nem közvetlen `A`-tömb-hozzáférés: a `0x007fc010` paraméteralapjához viszonyított `+0x90` és `+0x94`: vagyis a hívás alapján qshow `+0x388` és `+0x38c`: eltolásokra a függvény utasításaiban nincs közvetlen memóriaoperandus. Ezzel szemben a `0x007ffc90` a qshow `+0x388` címről olvas dupla pontosságú elemeket, a hosszt pedig `+0x38c >> 1` formában veszi; a `0x007fdd00` ugyanezt a pointer/hossz párt olvassa az index kiválasztásakor. A `+0x388/+0x38c` A-tömb és a `+0x3a8/+0x3ac` rekordvektor ezért külön mezőpár: a közös elemszám vagy a közeli cím önmagában nem bizonyít azonos tartalmat.

**Korlátos, indexfüggetlen ellenőrzés.** A `paszta.py` memóriakapus utasításpásztázását a qshow-hoz tartozó címeket is magában foglaló `0x007f0000`-`0x00810000` tartományra korlátoztam, a `+0x388`, `+0x38c`, `+0x3a8` és `+0x3ac` operandusokra szűrve. Tizenhat közvetlen mezőhivatkozás került elő: a `0x007fdd00`, `0x007fee70` és `0x007ffc90` helyeken mind olvasás; e tartományban e négy eltolás közvetlen író utasítását nem találtam. Ez csak erre a címtartományra és közvetlen operandusokra vonatkozik, nem zárja ki az azon kívüli írást, a segédhívás mellékhatását vagy a mezőcím közvetett előállítását.

**Cáfoló kísérlet.** Azt a jelöltet vizsgáltam meg, hogy a `0x007fc010` állítja elő a qshow `A` tömbjét. A hívó által átadott részmező, a callee által olvasott `+0xb4`/írt `+0x80` vektormező, a lokális `float` rendezési érték és a `0x007ffc90` különálló, `double`-elemes `+0x388` olvasata nem illeszkedik ehhez a közvetlen írói szerephez. A feltevés tehát a közvetlen mező-hozzáférésre nézve megbukott. A `0x007fbab0` vagy más hívott út közvetett mellékhatását ez nem cáfolja.

A keresés ellenpéldát is adott az eltolás-alapú azonosításhoz: a teljes `.text` pásztázás a `0x00514180` függvényben szintén megtalálta a `+0x388`, `+0x38c`, `+0x3a8` és `+0x3ac` írását (`0x00514859`-`0x00514914`). A függvényhez tartozó sztring-xrefek között a `Preferences`, dátumformátum és importbeállítás-nevek szerepelnek. Ez beállításkezelési út, nem bizonyíték qshow-adatra; a funkció pontos osztályát RTTI-vel nem azonosítottam. A cáfoló eredmény ugyanazzal a mércével ellenőrizve tehát megerősíti, hogy az azonos numerikus eltolás önmagában nem azonosít qshow-mezőt.

**A két út.** A út: a `0x00801cb0` hívási argumentumait és a `0x007fc010` mezőműveleteit utasításszinten követtem. B út: a qshow-kódterület memóriakapus, indexfüggetlen pásztázása ugyanazokat a közvetlen mezőhozzáféréseket a `0x007fdd00`, `0x007fee70` és `0x007ffc90` olvasóiba szűkítette; az önálló Ghidra-kimenet a `0x00801cb0` → `0x007fc010` hívást is jelzi. A két út a korlátozott állításban egyezik: a `0x007fc010` nem közvetlen `A`-tömb-íróként látszik. Egyik sem zárja ki a segédrutinon keresztüli közvetett írást, és futó qshow-n végzett második mérés nem készült; ezért ez a megállapítás **feltételes**.

| Állítás | Forrás |
|---|---|
| A `0x00801cb0` a qshow `+0x2f8`/`+0x2c8` mezőcímét adja át a `0x007fc010`-nek; az utóbbi `+0xb4 >> 1` ciklusszámot, három `float` visszatérési elemet, `+0x80` indexvektort és 0xf8 bájtos kártyarekordokat használ. | bináris (`0x00801cb0`, `0x007fc010`, `0x007fbab0`, `0x007fa650`) |
| A qshow `+0x388` tömb olvasója `double` elemekkel és a `+0x38c >> 1` hosszal. | bináris (`0x007ffc90`); csúszka-olvasó: `0x007fdd00` |
| A négy eltolás közvetlen operandusai a `0x007f0000`-`0x00810000` kódterületen; csak olvasások. | bináris (`paszta.utasitasok()`, `paszta.memoria_kapu()`; 16 egyező utasítás) |
| Azonos eltolások előfordulása a `0x00514180` beállításkezelési útban. | bináris (`0x00514859`-`0x00514914`; sztring-xrefek: `Preferences`, `0x00c7eafc`, valamint a `0x00c875c4`, `0x00c87604`, `0x00c877dc` környéki beállításnevek) |
| A qshow `+0x388` tömb valódi írója, elemeinek jelentése, dátumai, képei és forráskollekciói. | NINCS MEG |

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A kártyarendező közvetlenül nem az `A`-tömb írója; a gyűjtemények, képhalmaz, dátumkulcs, sorrend és elemazonosítók továbbra sincsenek meg. (2) ⛔ A korábban leírt kártyapálya-részletek mellett a teljes képkockánkénti út, időgörbe, rétegsorrend, háttér és kártyarajzolás nincs kész. (3) ⛔ A `timelinedot` és a csúszka statikus olvasási/rajzolási része dokumentált, de az `A` valódi szemantikája, a listaikon, a vezérlőhatások és a valós autoplay-ütem nyitott. (4) ⛔ A diavetítés tényleges futásidejű váltása és az Időrendbe visszatérő nézet/képindex nincs mérve.

**Nyitott.** A `qshow+0x388`/`+0x38c` tényleges írója, a tömb elemeinek előállítása és a token-/dátum-/képadatok kapcsolata **NINCS MEG**. A fenti negatív ellenőrzés csak a `0x007f0000`-`0x00810000` terület közvetlen utasításaira szól; a globális eltolásegyezések osztályazonosítása nélkül nem bizonyítanak qshow-adatot. A futó UI-val és valós adatállapottal végzett méréshez Wine kell, amely ezen a gépen nem érhető el. A `0x00419d10`/`0x00439a80` törzsek elkészültek; az általuk hívott segédek nyitott kérdéseit a 38.2.75 sorolja.

**Új kutatási jegyjavaslat.** Nincs; az `A` tömb írója és jelentése továbbra is a #5401 képlánc-/vezérlő-elfogadási pontjába tartozik.

#### 38.2.80 Futásidejű qshow-adatfelvételhez nincs helyi Colab-hozzáférés (#5401, 2026-10-23)

**Hozzáférési mérés.** A számítógép- és böngészőleltár ebben a Codex-munkamenetben üres (`apps=[]`, `browsers=[]`). A helyi eszközellenőrzés `qemu-i386`-ot talál, de `wine`/`wine64` programot nem; a qemu-s függvénypróba nem futó Win32 `qshow`-ablak, ezért nem adhatja meg annak élő mezőit vagy billentyűfókuszát.

**A mérőarchívum ellenőrzése.** A `~/.local/share/picasapy-meroadat/meroadat.tar` tagjegyzéke 944 bejegyzést tartalmaz; a teljes névlistában nincs `qshow`, `timeline`, `job-220`, `job-102`, `#5401` vagy `#5377` névvel azonosított mérési tétel. A `3229-lanc-sorrend` tag négy, azonos forrásképből készült szerkesztési sorrend-próba (`OLVASS-EL.txt`); nem Időrend-képhalmaz. Az archívumból nem bontottam ki semmit a `.bt` alá. A névlista-vizsgálat nem zárja ki, hogy egy más néven szereplő JPEG qshow-képkockát ábrázoljon; ilyen képek tartalmát nem ellenőriztem.

**A mai PicasaPy-állapot, kontrollált futás.** A `TimelineController.reload()` az index összes nem rejtett fotóját adja az év/hónap szerinti csoportosítónak (`src/picasapy/app/timeline_controller.py:73-90`); az EXIF `taken_at`, ennek hiányában a befagyasztott `sort_mtime_ns` adja a dátumot (`src/picasapy/timeline.py:47-90`). A QML `ListView`-t és korszakonkénti `GridView`-t rajzol (`src/picasapy/app/qml/PicasaPy/TimelineView.qml:61-125`), az Escape és a Bezárás az overlayt zárja (`TimelineView.qml:31-32,56-59`). A `Ctrl+5` gyorsbillentyű és a Nézet-menütétel jelenleg letiltott (`Main.qml:1861-1865`; `PicasaMenuBar.qml:1164-1168`). A Qt-mentes `build_periods()` kontrollált, öt rekordos futásának kimenete: `(2026, 10, (2, 4, 1))`, `(2025, 6, (3,))`, `(0, 0, (5,))`; a hónapcsoportok csökkenő sorrendűek, a dátum nélküli rekord a végére kerül, az azonos dátumú 2 és 4 rekord sorrendje megmarad. Ez a mai kód viselkedése, nem eredeti Picasa-paritásmérés.

| Állítás | Forrás |
|---|---|
| A mai csoportosító kontrollált kimenete, év/hónap- és képdátum-sorrendje, valamint az ismeretlen dátumú csoport helye. | mérés (`PYTHONPATH=src`, `build_periods()` öt kontrollált `TimelinePhoto` rekorddal, 2026-10-23; `timeline.py:93-132`) |
| A mai controller minden indexelt, nem rejtett fotót csoportosít; a menü és Ctrl+5 tiltott. | mérés (forrásleolvasás: `timeline_controller.py:73-90`, `Main.qml:1861-1865`, `PicasaMenuBar.qml:1164-1168`) |
| E munkamenetben nincs elérhető Colab-tab vagy más megnyitott alkalmazás/böngésző. | mérés (CUA-alkalmazás- és böngészőleltár: üres) |
| Helyben `qemu-i386` elérhető, `wine`/`wine64` nem. | mérés (`command -v`, 2026-10-23) |
| A mérőarchívum 944 tagbejegyzése között nincs név szerint qshow/Időrend/job-220/job-102 felvétel. | mérés (`meroadat.tar` teljes tagjegyzéke; név szerinti keresés) |
| A `3229-lanc-sorrend` készlet nem Időrend-fixture. | mérés (`meroadat.tar:3229-lanc-sorrend/OLVASS-EL.txt`) |
| A futó qshow `+0x50c` értéke, a `+0x388` tömb elemei és a hozzájuk rendelt képek/dátumok. | NINCS MEG |

**Két független út.** A út: a CUA-leltár nem mutat megnyitott böngészőt vagy alkalmazást, amin Colab-futás mérhető lenne. B út: a helyi végrehajtható-program ellenőrzés és a mérőarchívum tagjegyzéke sem ad futó Picasát vagy név szerint azonosított qshow-felvételt. A két út abban egyezik, hogy ebben a munkamenetben nincs hozzáférhető futásidejű minta; ez környezeti tény, nem a Picasa viselkedéséről szóló bizonyíték.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy az archívumban nincs azonosítható Időrend-mérés: mind a 944 tag nevét megvizsgáltam a qshow/Időrend és a korábbi job-azonosítók mintáira. Név szerint egyező tétel nem volt. A cáfolat határa a fájlnevezés: a más néven levő képek képtartalma nem lett átvizsgálva, így az eredmény nem állítja, hogy az archívum minden képe irreleváns.

**Bizonyítottsági fok.** **Megerősített** a hozzáférési hiány a fenti, egymástól különböző környezet- és archívum-ellenőrzésre nézve. A termékviselkedés és a qshow mezők tényleges értékei továbbra is **nyitottak**; ebből a körből azokhoz új bináris- vagy futásidejű lelet nem született.

**A #5401 „Kész, ha” pontjai.** (1) ⛔ A tokenindex, forráshalmaz, képek, dátumkulcs, sorrend és elemszám nem lett futó qshow-n megmérve. (2) ⛔ Nem készült új képkocka- vagy mozgásmérés. (3) ⛔ A vezérlők, `A`-tömb-jelentés és tényleges autoplay-periódus nem lett futó állapotban megmérve. (4) ⛔ Nem készült Space/Escape előtti-utáni nézet- és képindexfelvétel.

**Nyitott; megszerzésének pontos útja.** A következő méréshez ugyanabban az elérhető Colab-futásban kell: (a) rögzíteni egy előre ismert, eltérő kép- és dátumadatú forráskészletet, valamint azt, hogy mappa, album vagy Picture Tray van kiválasztva; (b) a qshow megnyitásakor és a vezérlők használata után kiolvasni a `qshow+0x50c`, `+0x2f8` kiválasztott `0xf8` rekordját, a `+0x388`/`+0x38c` tömböt és a CThumbDB-token → `CSlice+0x64` → képrekord kapcsolatot; (c) azonos futásban képkockákat és a Space/Escape előtti-utáni nézetet, kollekciót és indexet rögzíteni. Csak ezek az adatok döntik el a 38.2.63-79 nyitott pontjait; újabb, azonos kérdésű statikus eltoláskeresés nem helyettesíti ezt a mérést.

#### 38.2.81 A job-239 qshow-felvétele: látható gyűjtemények, sorrend, felirat és kilépés (#5401, 2026-10-24)

**Hatókör és forrás.** A helyben átadott `.bt/job-239/` teljes képsorát átnéztem a `feladat.md` lépéssorával és mintajegyzékével együtt; új diszasszemblálás vagy `.text`-pásztázás nem történt. A mappában 30 PNG van, míg a `feladat.md` 29 műveletet sorol: a `kepernyo__01.png` az induló képernyő, a `kepernyo__29.png` fekete átmeneti kép Escape után, a `kepernyo__30.png` pedig a két másodperccel későbbi visszatért Picasa-könyvtár. A képernyőfelvétel 1280×1024-es Wine-asztalon készült. A táblázat a képernyőn olvasható adatot és a feladatban megadott fixture-t külön kezeli.

##### §1 A látható katalógus és a Right billentyűvel bejárt sorrend

A Picasa-könyvtár `kepernyo__02.png` képén az `Albums (1)` alatt `Recently Updated (24)`, a `Folders (5)` alatt pedig `PicasaTeszt (24)` és a négy fixture-mappa látszik. A négy mappaszám egyezik a feladat mintájával:

| Fixture-mappa | Fájlok a `feladat.md` szerint | Darab | qshow-felirat a képsorban |
|---|---|---:|---|
| `2009_majus` | `2009_majus_01.jpg` | 1 | `2009_majus` / `May 2009` |
| `2014_november` | `2014_november_01.jpg`, `_02.jpg`, `_03.jpg` | 3 | `2014_november` / `November 2014` |
| `2019_marcius` | `2019_marcius_01.jpg`-`_07.jpg` | 7 | `2019_marcius` / `March 2019` |
| `2021_eltero_fajlido` | `2021_eltero_fajlido_01.jpg`, `_02.jpg` | 2 | `2021_eltero_fajlido` / `August 2021` |

A `Ctrl+5` után induló qshow kezdetben a 2009-es csoportot mutatja. Az ismételt `Right` léptetés képernyőn látható sorrendje: `2009_majus` → `2014_november` → `2019_marcius` → `2021_eltero_fajlido` → `PicasaTeszt` → `Recently Updated`. A négy fixture-mappa tehát ebben a futásban időrendben halad; a két 2026. októberi csoport sorrendje `PicasaTeszt`, majd `Recently Updated`. Ez a futásban látott sorrend, nem az upstream rendezőkulcs azonosítása. A qshow kártyájának jobb felső felirata a mappanév és az angol hónap+év; az előző nagyméretű kártyán a mappanév és a kép teljes dátumideje is megjelenik (például `2009_majus` / `2009-05-14 10:00`, majd `2014_november` / `2014-11-02 15:30`, végül `2019_marcius` / `2019-03-08 09:15`).

A 2021-es kontroll különválasztja az EXIF-dátumot a fájlidőtől: mindkét fixture-fájl EXIF-je `2021:08:20`, fájlidejük viszont `2023-01-01 12:00:00`; a qshow felirata `August 2021`. Ez a minta cáfolja, hogy a látott 2021-es címkét kizárólag a fájlidő adja. A belső Picasa-mező ettől még nincs azonosítva: a felirat EXIF-kompatibilis, de nem bizonyítja, hogy a qshow közvetlenül az EXIF-mezőt olvassa.

A négy fixture-mappa mellett a képsorban ténylegesen szerepel a `PicasaTeszt (24)` mappa és a `Recently Updated (24)` album is; ezeket a 13 felsorolt mintafájl nem írja le. Ezért a felvétel a **látható** forráscsoportokat és a fixture-mappák sorrendjét megadja, de nem adja meg az összes csoport qshow-tokenjét, a 24 elemű listák tényleges képeit, illetve az átfedést a gyűjtemények között. A qshow `+0x2f8` rekordjából származó `+0x50c` tokenindex továbbra is a CThumbDB `token` sztring-oszlopát indexeli; a konkrét token és az általa kiválasztott `CSlice+0x64` képrekord-lista nincs meg (38.2.63 §1/a, 38.2.74; `0x008018a0`, `0x004406f0`, `0x004dca40`).

##### §2 Animáció és időzítés: mit igazol a sűrűségében korlátozott képsor

A qshow-képek a kártyalánc tényleges mozgását és a háttér változását mutatják; a billentyűs `Right` után az aktív mappanév és hónapfelirat a következő csoportra vált. A `feladat.md` minden vizsgált lépéshez azonnali, 0,5 másodperces és összesen 2,5 másodperces képernyőképet kér. Az első három mappaváltásnál az azonnali és a +0,5 másodperces képkocka láthatóan eltér, a +0,5 és +2,5 másodperces képkocka viszont az ellenőrzött qshow-területen közel azonos. A negyedik átmenetnél (`2021_eltero_fajlido` → `PicasaTeszt`) a cím a +0,5 másodperces képen vált át; a `Recently Updated`-re lépésnél a háttér is megváltozik. Ez azt igazolja, hogy a bemutató animált, és az adott minta több váltása 2,5 másodpercre már közel állandó képet ad. A képsor nem méri a pontos animációhosszt: a köztes képkockák hiánya miatt nem állítható, hogy a mozgás pontosan 0,5 vagy 2,5 másodpercig tart.

A binárisból már ismert részeredmények változatlanok: a kártyagörbe `0x007fbab0` képlete QEMU-val ellenőrzött (38.2.61); a `0x00802230` véletlen eltolása és a `0x007fff30` transzformációi szintén QEMU-val mértek (38.2.62); a csúszka x→index választása `0x007fdd00`-ban, a pontok kirajzolása pedig a `0x007ffc90` útján dokumentált (38.2.77-78). Ezek a statikus/QEMU-eredmények és a látható mozgás egymással összeférnek, de nem kötik a teljes képkockánkénti képtartalmat a transzformációkhoz, nem adják meg a háttér teljes rajzolási útját, és nem töltik ki az `A` tömb tartalmát.

Az `0x00802060` az eltelt QPC-másodpercet a `Preferences\SlideshowEffectTime` `T` küszöbével hasonlítja össze, majd a léptető utat hívja; a callback címe `0x00803ab0` (38.2.34 §1). A job-239 minden továbblépését kézzel küldött `Right` előzte meg, ezért az automatikus lejátszás tényleges periódusát vagy a futásban aktív `T` értéket ez a képsor **nem méri**.

##### §3 Vezérlők, Home/End és visszatérés

A `Right` billentyű legalább a négy fixture-csoporton végigléptet, majd a két látható októberi csoportot is eléri. A `timelinedot`, `sliderthumb`, `startbutton`, kilépőgomb és listaikon látható, de a feladat nem kattint rájuk és nem húzza a csúszkát; a pontok dátumjelentése és ezek interakciói ezért továbbra is nyitottak. A `Space` nem szerepel a lépéssorban, így a diavetítésbe váltást ez a mérés nem ellenőrzi.

A `Home` és `End` a `Recently Updated` utolsóként látható csoportnál került megnyomásra. A `kepernyo__22.png`-`kepernyo__28.png` képei az ellenőrzött qshow-területen pixelre azonosak: ebben a lépéssorban egyik gomb után sem látható változás. Ez nem bizonyítja, hogy a billentyűágak nincsenek bekötve, mert a futásadat nem rögzíti a qshow fókuszát és az utolsó csoportban az `End` eleve nem szükségszerűen változtat állapotot; a `Home` tényleges hatása külön, fókuszt is rögzítő mérésre vár.

Az `Escape` után a `kepernyo__29.png` fekete átmeneti kép, a `kepernyo__30.png` pedig visszatér a Picasa főablakának `PicasaTeszt` mappanézetére. A belépés előtti `kepernyo__02.png` ugyanezt a mappanézetet mutatja. Így a qshow bezárása és a mappanézethez való visszatérés közvetlenül megfigyelt; a pontosan kijelölt kép és index nincs kiolvasható. A méréssorban Space nem volt, ezért a diavetítésből való visszatérés nem következtethető ebből.

##### §4 Független utak, cáfoló kísérlet és bizonyítottság

**A út - Picasa-katalógus felülete.** A `kepernyo__02.png` főablakának oldalsávja külön mutatja az `Albums (1)`/`Recently Updated (24)` és a `Folders (5)` listát, benne a négy fixture-mappa darabszámával. Ez a qshow-tól külön képernyőréteg azonosítja a látható kategóriák típusát és a négy almappa darabszámát.

**B út - qshow-képsor és fixture-metaadat.** A `kepernyo__05.png`-`kepernyo__24.png` felvételek a kategóriák feliratait és a Right-léptetés sorrendjét adják. A `feladat.md` EXIF/fájlidő táblája ettől külön adja a tesztképek dátumait; a 2021-es címke az EXIF-hónappal egyezik, a 2023-as fájlidővel nem. A két út a négy fixture-mappa nevében, darabszámában és látható év/hónap-sorrendjében egyezik. A bináris út a token→CThumbDB→CSlice-lista mechanizmust és a qshow-lista sorrendtartó átvitelét támasztja alá, de az élő tokenek és konkrét képek hiányában nem azonosítja ugyanazt a fotólistát (38.2.63 §1/a, §4; 38.2.74; `0x008018a0`, `0x004406f0`, `0x004dca40`).

**Cáfoló kísérlet.** Megpróbáltam cáfolni (a) azt, hogy a négy fixture-mappa a teljes megjelenő forráskészlet, és (b) azt, hogy a 2021-es csoportot fájlidő rendezi. Az első ellenpélda a főablakban és qshow-ban egyaránt látható `PicasaTeszt` és `Recently Updated` csoport. A másodikat a két, 2023-as fájlidejű, de 2021. augusztusi EXIF-ű kép és a qshow `August 2021` felirata adja. Mindkét ellenpélda visszakereshető a képernyőn és a mintajegyzékben; a cáfolat ugyanazzal a mércével ellenőrizhető. Az eredmény csak a job-239 ezen Picasa-katalógusára vonatkozik.

**Bizonyítottsági fok: feltételes** a #5401 egészére. A felsorolt feliratok, látható csoportdarabszámok, a Right-sorrend, a 2021-es EXIF/fájlidő-eltérés és az Escape utáni mappanézet mért megfigyelések. A teljes forráshalmaz, a qshow-tokenek, az `A` elemei és dátumjelentése, a kártyákhoz kötött összes képrekord, a teljes képkocka-képlet, a pontos animációs idő, a kattintás/húzás és a Space/diavetítés-visszatérés viszont ebből az egy, nem izolált futásból nem bizonyított.

| Állítás | Forrás |
|---|---|
| Négy fixture-mappa neve és darabszáma (1/3/7/2), továbbá a `PicasaTeszt (24)` mappa és `Recently Updated (24)` album láthatósága. | mérés (`job-239/kepernyo__02.png`; `job-239/feladat.md`) |
| qshow címkék és Right-léptetés sorrendje: 2009 → 2014 → 2019 → 2021 → PicasaTeszt → Recently Updated. | mérés (`job-239/kepernyo__05.png`-`__24.png`) |
| 2021. augusztusi címke két 2023. január 1-i fájlidő mellett. | mérés (`job-239/feladat.md`; `kepernyo__13.png`-`__17.png`) |
| A képsor azonnali, +0,5 és +2,5 másodperces mintavételi rendje. | mérés (`job-239/feladat.md`; `kepernyo__07.png`-`__15.png`) |
| qshow `+0x50c` élő tokenértéke, `+0x388` A-tömb elemei és a tokenekhez tartozó képrekordok. | NINCS MEG (`0x008018a0`, `0x004406f0`, `0x004dca40`) |
| A `timelinedot` dátumértéke, a kattintás/húzás felhasználói hatása, az aktív autoplay `T` és callback-periódus. | NINCS MEG (`0x007fdd00`, `0x007ffc90`, `0x00802060`, `0x00803ab0`) |
| Space utáni diavetítés és az abból visszaálló kép/index. | NINCS MEG (`0x00801270`, `0x00803110`, `0x00983270`; a job-239 nem küldött Space-t) |
| Escape után a Picasa `PicasaTeszt` mappanézetének visszaállása; a képkijelölés/index. | mérés (`job-239/kepernyo__02.png`, `__29.png`, `__30.png`) / NINCS MEG (pontos képkijelölés) |

##### §5 A #5401 „Kész, ha” pontjai és a #5377 átadása

1. ⛔ **Képlánc/forráshalmaz/sorrend/darabszám:** a négy almappa, a darabszámuk, a jobb-billentyűvel látott időrend és két további októberi csoport ismert; a teljes token-, kép- és albumtagság, az upstream dátumkulcs és az `A` tömb konkrét elemei nyitottak.
2. ⛔ **Mozgás/időzítés/rajzolás:** a képsor megerősíti a mozgó kártyaláncot és részleges stabilizálódást; a teljes képkocka→transzformáció→réteg kapcsolat, a pontos animációhossz és a háttér teljes rajzolási útja nincs meg. A korábbi QEMU-képletek a 38.2.61-62-ben maradnak.
3. ⛔ **Vezérlők:** a Right és Escape megfigyelt; a látható pontok/csúszka/gombok nincsenek interakcióval mérve; a Home/End próbája nem döntött; Space és automatikus léptetés nincs mérve.
4. ⛔ **Diavetítés/kilépés/visszatérés:** Escape után a mappanézet visszatérése megfigyelt, de Space nem volt a lépéssorban és az Escape utáni képindex ismeretlen.

| Eredeti | Nálunk (forrásállapot) | Teendő a #5377-ben |
|---|---|---|
| A `0x005e8a70` Időrend-belépése qshow-t épít; a job-239-en a Right 2009/05, 2014/11, 2019/03, 2021/08, 2026/10 csoportokat mutatott, a katalógusban pedig külön album és mappacsoportok látszottak. A `0x008018a0` tokenből épít sorrendtartó listát; a token neve és teljes elemsora nyitott. A mozgás rész-képletei: `0x007fbab0`, `0x00802230`, `0x007fff30`; csúszka/pont: `0x007fdd00`, `0x007ffc90`. | A `TimelineController.reload()` a rejtett szűrés után `folder_path` szerint csoportosít, a kártyadátumot a mappa legkorábbi ismert `record_date`-jából veszi, dátum szerint növekvő sorrendbe teszi és kártyánként legfeljebb négy bélyeget ad át (`src/picasapy/app/timeline_controller.py:161-252`). A `TimelineView.qml` Right/Left átmenete 2000 ms, a csúszka felengedése 4000 ms; Space a kiválasztott mappa diavetítés-modelljét kéri, Escape lezárja a nézetet (`TimelineView.qml:85-95,105-109,210-223`). Ez forrásleolvasás, nem e körben futtatott PicasaPy-mérés. | A #5377 teljes, becslésmentes követelménylistája még nem írható át: qshow-token/képlista, dátumtömb, `A`, vezérlőhatások és Space utáni visszatérő kép hiányzik. Ezeket ugyanazon kontrollált eredeti futásból kell kinyerni és képkockákkal összevetni. A mostani felvétel alapján rögzíthető a négy almappa neve/darabszáma, a látható csoportsorrend, hónapfelirat, a `PicasaTeszt`-/`Recently Updated` többlet és az Escape utáni mappanézet. |

**Nyitott; megszerzésének pontos útja.** A meglévő Ghidra-kimenetek elegendők a már leírt statikus utakhoz; új Ghidra-cím nem szükséges. Egy elkülönített eredeti Picasa-futásban rögzíteni kell a forráskatalógust, a qshow `+0x50c` mezőjét, a `+0x2f8` kiválasztott `0xf8` rekordját, a `+0x388`/`+0x38c` tömböt és a CThumbDB-token → `CSlice+0x64` → képrekord egyeztetést; külön futásban Space után és Escape után a nézetet, gyűjteményt és képindexet. A vezérlőgombok/húzás és az autoplay csak az aktív qshow fókusz, dátum- és időmezők egyidejű rögzítésével dönthető el. Új kutatási jegy nem kell: mindez továbbra is a #5401 része.

#### 38.2.82 A job-240 mérése: Space, Escape, automatikus léptetés és újranyitás (#5401, 2026-10-24)

**Hatókör és mérési elrendezés.** A helyi .bt/job-240/feladat.md lépéssora a korábban használt idorend mintakészleten előbb Ctrl+5 után öt, egyenként 3 másodperces beavatkozás nélküli mintát készít; utána kétszer Right, Space, 3 és további 5 másodperc várakozás, Escape, majd 2 másodperc múlva még egy Ctrl+5 és 3 másodperc várakozás következik. Az eredeti futásadat a .bt/job-240/eredmeny.json és allapot.json; a felvétel 23 képe a kepernyo__01.png-kepernyo__23.png. A futás 2026-10-24 07:38:30 UTC-kor készült. Az alábbi megállapítások kizárólag erre a mintakészletre és futásra vonatkoznak.

**Automatikus léptetés.** A Ctrl+5 utáni, 3 másodpercenként rögzített öt kép (kepernyo__06.png-kepernyo__10.png) pixelről pixelre azonos: a qshow nyitva marad, és ugyanaz a 2009_majus / May 2009 kártya látszik. E 15 másodperces megfigyelési ablakban nem történt látható automatikus kártyaléptetés. Ez nem állapítja meg a qshow minden módjának viselkedését vagy egy hosszabb időszak ütemét. A 0x00802060 függvény QueryPerformanceCounter-időt hasonlít a Preferences\SlideshowEffectTime értékhez (38.2.34); a jelenlegi beállításérték és a qshow e méréskori időzítőállapota nincs meg. A Space utáni 3 és összesen 8 másodperces felvétel (kepernyo__16.png-kepernyo__17.png) szintén pixelazonos, de ez a két minta nem méri meg általánosan az automatikus diaváltás ütemét.

**Space.** A két Right után a 2019_marcius kártya látszik; Space-re a kepernyo__15.png már a OneUp/diavetítési felületet mutatja. A képen a 2019_marcius csoport első képe, 1/7 sorszámmal és 2019-03-08 09:15 dátummal szerepel; a felületen az Exit Slideshow, Timeline és Display Time 3 seconds felirat olvasható. A 3 és 8 másodperces képen ugyanaz az 1/7 kép marad. Ez bizonyítja a diavetítési felület megnyitását, de önmagában nem bizonyítja, hogy a képkockák automatikusan lépnek vagy hogy a három másodperces kijelzés a tényleges futási ütem.

A binárisban a 0x00801270 billentyűkezelő Space-ágát a qshow +0x3bb állapota választja szét: az egyik út a 0x00801130, a másik a 0x00803110 felé halad. A 38.2.67-ben követett sikeres elemút a 0x009833a0 gazdaobjektum-cseréjéhez és a QDrawable → OneUpUI felületváltáshoz vezet. A felvétel a megjelenő OneUp/diavetítési felülettel egyezik; az aktuális képkocka továbblépését nem igazolja.

**Escape és a második Ctrl+5.** Escape után, a kepernyo__18.png és __19.png képeken a Picasa fő böngészőnézete látható, a bal oldali listában kijelölve marad a 2019_marcius mappa, alul 7 kép szerepel; az allapot.json szerint a qshow ablak eltűnt. Egyik képen sincs egyedi fotókijelölés vagy képindex, ezért a visszaadott fotópozíció NINCS MEG. A 2 másodperces várakozás után küldött második Ctrl+5 és az azt követő 3 másodperc alatt (kepernyo__20.png-kepernyo__21.png) qshow nem nyílik meg; az allapot.json ablaklistája is csak a Wine desktopot és a Picasa 3-at tartalmazza. E futás tehát nem mutat újranyitott kártyát, így nem dönti el, melyik kártyán indulna egy sikeres újranyitás.

A bináris Escape-útját a 0x00801270 a 0x007fb820 kilépési rutinba vezeti; az a gazdaobjektum vtable +0x14 kilépési hívását használja (38.2.64, 38.2.68). A futásban mért qshow-bezáródás ezzel összhangban van. A ténylegesen kijelölt visszatérési fotót vagy későbbi újranyitási pozíciót ez a bináris út nem adja meg.

**A két független út és bizonyítottság.** A út: a 0x00801270, 0x00801130, 0x00803110 és 0x009833a0 diszasszemblye a Space állapotágát és a sikeres OneUpUI-gazdacserét mutatja; a 0x007fb820 gazda-kilépési hívása az Escape útját adja. B út: a job-240 képein Space után megjelenik az OneUp/diavetítési felület, Escape után pedig eltűnik a qshow, és a fő böngészőnézet látszik. A szűk állítás - Space megnyitja a diavetítési felületet, Escape bezárja a qshow-t - a két út között egyezik, ezért **megerősített**. A mappakijelölés megmaradása, a második Ctrl+5 eredménye, az általános automatikus ütem és a fotóindex csak egyetlen futás megfigyelése vagy egyetlen statikus út alapján állítható; ezek **feltételesek vagy nyitottak**, nem általánosíthatók.

**Cáfoló kísérlet.** Azt a feltevést ellenőriztem, hogy az Időrend a Ctrl+5 után ebben a futásban magától másik kártyára lép. Az öt, 3 másodpercenként készült képet pixelazonosan összevetve mind azonos kártyát mutat, ezért a feltevés erre a 15 másodperces mintára cáfolódik. Azt is ellenőriztem, hogy a második Ctrl+5 után megjelenik-e új qshow: a kepernyo__20.png-__21.png és az allapot.json egyaránt qshow nélküli állapotot mutat. Ezek negatív eredmények csak a rögzített futásra érvényesek; nem bizonyítják, hogy az Időrend általában nem léptet vagy nem nyitható újra.

**Bizonyíték.**

| Állítás | Forrás |
|---|---|
| Ctrl+5 után a 15 másodperces megfigyelési ablakban nem változott a látható kártya. | mérés (job-240, kepernyo__06.png-kepernyo__10.png; pixelazonos képek) |
| Space a 2019_marcius csoport 1/7 képével megnyitja a OneUp/diavetítési felületet. | mérés (job-240, kepernyo__15.png); bináris (0x00801270, 0x00801130, 0x00803110, 0x009833a0) |
| A Space után 3 és 8 másodperccel rögzített kép azonos; általános automatikus ütem ebből nem következik. | mérés (job-240, kepernyo__16.png-kepernyo__17.png; pixelazonos képek) |
| Escape után eltűnik a qshow, és visszatér a fő böngésző; a kijelölt mappa 2019_marcius. | mérés (job-240, kepernyo__18.png-kepernyo__19.png, allapot.json); bináris Escape-út (0x00801270, 0x007fb820) |
| Escape után visszaállított fotóindex. | NINCS MEG |
| A második Ctrl+5 után újranyílt Időrend-kártya. | mérés (job-240, kepernyo__20.png-kepernyo__21.png): ebben a futásban nem nyílt qshow |
| A következő automatikus képlépés pontos általános üteme. | NINCS MEG; a 0x00802060 csak a QPC és Preferences\SlideshowEffectTime összehasonlítását adja, a futásidejű paraméterek hiányoznak |

**A #5401 „Kész, ha” pontjai.**

1. ⛔ A mappa/kártya csoportsorrend job-239-ből ismert, de a qshow teljes forrás-tokenje, valamennyi képe és teljes rendezési kulcsa továbbra sincs meg.
2. ⛔ A részmozgás-képletek korábbi szakaszokban szerepelnek; a teljes képkockánkénti pálya, időgörbe és rétegrajzolás nincs feltárva. A job-240 nem pótolja ezt.
3. ⛔ A Space/Escape részleges látható hatása új bizonyítékot kapott; a dátumcsúszka leképezése, timelinedot/listaikon, minden vezérlőhatás és az autoplay általános üteme nyitott.
4. ⛔ Space a mért 2019_marcius csoport első képével nyitja meg a diavetítési felületet. Escape a fő böngészőbe tér vissza, a mappakijelölés 2019_marcius marad, de az egyedi képindex NINCS MEG; a második Ctrl+5 után ebben a futásban nem nyílt qshow.

**Nyitott és megszerzésének útja.** Nincs új Ghidra-kérés: a kapcsolódó Space-, Escape- és időzítőcímek meglévő elemzése megvan. A teljes képhalmazhoz és kártyához az aktív qshow +0x50c mezőjét, a +0x2f8 kiválasztott rekordot és a +0x388/+0x38c tömböt kell a job-239 mintaképeivel egyeztetni. Az automatikus léptetés üteméhez ismételt, időbélyegzett képkockasor kell több, eltérő Display Time-beállítással, a play/stop állapot rögzítésével. A Space utáni képlépés és az Escape utáni folytatási index megállapításához az ismert 2019_marcius/1-7 képeket egyedileg követő futás és a fő böngésző kijelölésének rögzítése szükséges. A második Ctrl+5 újranyitási kártyáját csak olyan futásból lehet megállapítani, amelyben a második parancs ténylegesen qshow-t nyit; a mostani felvétel erre nem szolgáltat adatot.

**Új kutatási jegyjavaslat.** Nincs; a nyitott kérdések a #5401 elfogadási pontjaihoz tartoznak.

#### 38.2.83 A job-241 visszatérése, újranyitása és bal nyila (#5401, 2026-10-24)

**Mérési alap.** A helyi `.bt/job-241/` feladat 21 képernyőképe 1280×1024-es Wine-asztalon készült; a `feladat.md` közvetlen qshow-belépést, három `Right`-ot, `Escape`-et, újabb `Ctrl+5`-öt, `Left`-et és második `Escape`-et rögzít. A futás az `eredmeny.json` szerint 2026-10-24 08:38:33 UTC-kor zárult. A következtetések erre a lépéssorra vonatkoznak.

**Escape után kijelölt mappa és bélyegkép.** A qshow harmadik `Right`-ja után a `kepernyo__11.png`-`__12.png` a `2021_eltero_fajlido / August 2021` kártyát mutatja. Az első `Escape`-et követő `kepernyo__14.png`-`__15.png` képen a bal oldali mappalistában a `2021_eltero_fajlido` sor kijelölt; a mappa első bélyegképén kijelölőkeret látszik, az alsó állapotsorban pedig `2021_eltero_fajlido_01.jpg` olvasható. Tehát **ebben a futásban** a qshow az utoljára mutatott csoportot adta vissza kijelölt mappaként, azon belül az első képet.

**A második `Ctrl+5`.** A `kepernyo__16.png` átmeneti, a `kepernyo__17.png` stabil qshow-képkockán a felirat `2009_majus / May 2009`. A qshow a korábban kijelölt `2021_eltero_fajlido` csoport helyett az első, 2009-es kártyával nyílik újra. A `kepernyo__21.png` második `Escape` utáni főablakában a `2009_majus` mappa és az `2009_majus_01.jpg` bélyegkép van kijelölve. Ez a job-240 eredményétől különböző út: ott előbb Space vitte a OneUp/diavetítési felületre, onnan történt Escape, és azután a `Ctrl+5` nem nyitott qshow-t (38.2.82). A két mérés eltérő előzményű; az egyik nem cáfolja a másikat.

**Bal nyíl.** A `Ctrl+5` után a második qshow a kezdő `2009_majus` kártyán áll. A `kepernyo__17.png`, `__18.png` és `__19.png` RGB-képei pixelre azonosak; a `Left` után ezen az első kártyán nem látható változás. Ez a próba **nem dönti el**, hogy a bal nyíl középső kártyáról az előzőre léptet-e: az első kártyán nincs korábbi elem, és a felvétel nem rögzíti külön a qshow fókuszát.

**Összevetés a binárissal.** A `0x00801270` a qshow `WM_KEYDOWN` kezelője: az `Escape` (`0x1b`) a `0x007fb820` rutinra ágazik, a bal nyíl (`0x25`) pedig a `0x008011b0` útját hívja. A `0x008011b0` timeline-ágában a `[this+0x3b8]` jelző nem nulla értéke esetén a `0x007fd0c0` kapja a kiválasztott rekord `[+0x30]` mezőjét és a `0x00cf3a48` címen tárolt `2.0f` értéket (38.2.63 §2, 38.2.66). Ez a statikus út a billentyűkezelést és a mozgásfrissítő hívását igazolja; a `2.0f` előjeléből önmagában nem következik a felületen látható irány vagy az első elem határviselkedése.

Az `Escape` a `0x007fb820`-en át a qshow gazdaobjektum virtuális `+0x14` kilépési hívásáig jut (38.2.64, 38.2.68; köztes híváshely: `0x007fb998`-`0x007fb9df`). A futásban a `qshow` ablak eltűnik, és a Picasa böngészőablaka marad. A bináris nem tartalmazza a job-241 során kijelölt `2021_eltero_fajlido_01.jpg` vagy `2009_majus_01.jpg` fájlnevet; a konkrét mappa- és bélyegkép-kijelölés mért felületi állapot. A második `Ctrl+5` induló nulla indexe a 38.2.63 §1/a-ban szerepel (`0x008037e0` → `0x008018a0(0)`); a mostani 2009-es felirat összhangban van a job-239 első kártyájával, de nem bizonyítja, hogy más belépési állapotban is mindig ugyanez nyílik.

**A két független út.** A út: a job-241 képsora közvetlenül mutatja a kijelölt mappát/bélyegképet, a második qshow-kártyát és a `Left` utáni változatlanságot; a JSON külön megerősíti, hogy az Escape után a `qshow` ablaklistáról eltűnik, a második `Ctrl+5` után visszakerül. B út: a PE utasításszintű olvasata és a korábban feldolgozott Ghidra/vtable-út a `0x00801270` Escape- és balnyíl-ágát, illetve a qshow gazda-kilépési hívást azonosítja. A két út egyezik abban, hogy Escape lezárja a qshow-t és a Left a timeline mozgásútjára jut; **nem** adnak két független bizonyítékot a konkrétan kijelölt fotónévre vagy a második megnyitás 2009-es kártyájára. Ezek a job-241 egyetlen futásában megfigyelt tények.

**Cáfoló kísérlet.** Azt a hipotézist próbáltam cáfolni, hogy az újbóli `Ctrl+5` a visszatéréskor kijelölt 2021-es csoportnál folytatja a qshow-t. A `kepernyo__17.png` ehelyett `2009_majus / May 2009` feliratot mutat, a főablakba való második visszatérés pedig a `2009_majus_01.jpg`-t jelöli ki. A képkockákat azonos mércével ellenőriztem: `ImageChops.difference(17, 18).getbbox()` és `ImageChops.difference(17, 19).getbbox()` egyaránt `None`, tehát a `Left` után a kezdő kártyán nincs képpontváltozás. A cáfolat csak a tesztelt futás „folytatja a 2021-es kártyán” hipotézisét dönti meg; nem bizonyítja az újranyitási szabály általánosságát vagy a Left középső kártyán való hatását.

**A cáfoló ellenőrzés ellenőrzése.** A friss képcáfoló kör azt vetette fel, hogy a `kepernyo__18.png` fekete átmeneti képkocka. Az eredeti fájlok bájtszintű ellenőrzése ezt az ellenvetést megcáfolja: a 17., 18. és 19. PNG SHA-256 lenyomata egyaránt `ca7dbea6ade579789c6c2412d559331d5675c807c2b70302c3db0425313d96a3`; a 18. kép külön megnyitva is a `2009_majus` kártyát mutatja. A fekete képkockára alapozott ellenérv téves riasztás; a három kép azonossága megmarad. A felvétel ettől még nem rögzíti külön, hogy a qshow kapta-e a billentyűeseményt, ezért a `Left` belső hatása nyitott.

**Bizonyítottsági fok: feltételes.** A mappakijelölés, az első bélyegkép fájlneve, a 2009-es újranyitási kártya és a kezdő kártyán megfigyelt Left-változatlanság képernyőképen mért, egy futásra érvényes adat. Az Escape- és billentyűhívási utak binárisból olvashatók, de a konkrét kijelölési adatot nem hordozzák.

| Állítás | Forrás |
|---|---|
| Első Escape után a `2021_eltero_fajlido` mappa és első bélyegképe, `2021_eltero_fajlido_01.jpg` kijelölt. | mérés (`.bt/job-241/kepernyo__14.png`-`__15.png`, alsó állapotsor) |
| A második `Ctrl+5` után a qshow `2009_majus / May 2009` kártyán látható. | mérés (`.bt/job-241/kepernyo__16.png`-`__17.png`) |
| `Left` után az első kártya képe nem változik; 17/18/19 pixelre azonos. | mérés (`.bt/job-241/kepernyo__17.png`-`__19.png`; pixelkülönbség `None`) |
| A második Escape után `2009_majus` és `2009_majus_01.jpg` van kijelölve. | mérés (`.bt/job-241/kepernyo__21.png`) |
| Escape/Left billentyűág a qshow kezelőből a `0x007fb820` / `0x008011b0` útra jut. | bináris (`0x00801270`, `0x007fb820`, `0x008011b0`) |
| Timeline balnyíl-ág a `0x007fd0c0` hívásban `2.0f` értéket használ. | bináris (`0x008011b0`, `0x00cf3a48`, `0x007fd0c0`) |
| Bal nyíl hatása nem kezdő kártyán; újranyitás minden előzményben; visszatérő képindex más képcsoportban. | NINCS MEG |

**A #5401 „Kész, ha” pontjai e mérés után.** (1) ⛔ A teljes forrás-token, képlista, dátumkulcs és gyűjteményenkénti képszám továbbra sincs meg. (2) ⛔ A teljes képkockamozgás, időgörbe és rétegrajzolás továbbra sem zárult le. (3) ⛔ A Left csak a kezdő kártyán lett próbálva; a többi vezérlő és az autoplay üteme nyitott. (4) ⛔ A közvetlen qshow-Escape utáni mappa és első bélyegkép, valamint az újbóli `Ctrl+5` kezdőkártyája ebben a mintában ismert; a `Space` utáni folytatás és az általános visszatérési index továbbra sincs meg.

**Nyitott; következő pontos mérés.** A Left hatásához a qshow-ban `Right`-tal át kell lépni az első kártyáról a következőre, majd azonos időközzel képet kell készíteni a `Left` előtt és után; ezzel elkerülhető az első elem határhelyzete. A második `Ctrl+5` viselkedését a közvetlen qshow-Escape és a Space/diavetítés-Escape út külön futásaiban kell összevetni. Új Ghidra-kérés nem szükséges ehhez a két kérdéshez: a statikus ágak meglévők, a hiányzó bizonyíték futásidejű.

**Új kutatási jegyjavaslat.** Nincs; a nyitott pontok továbbra is a #5401 elfogadási feltételeihez tartoznak.

#### 38.2.84 A #6532 helyi bináris-újraellenőrzése és az eredeti videó hiánya (2026-11-04)

**Történeti státuszfrissítés (2026-11-10):** a „videó hiánya” megállapítás lezárva: 38.2.85 és 38.2.101 (job-373/job-446 videók elérhetők). A teljes visszafejtés nyitott pontjainak aktuális mérlege a 38.2.105.

**Hatókör.** Ez a bejegyzés a munkamenetben újra ellenőrzött bináris hívásutat és a jelenlegi PicasaPy-forrás állapotát rögzíti. Az eredeti Picasa futtatásához és folyamatos videófelvételéhez ebben a munkamenetben nem volt elérhető Colab-tab vagy más végrehajtó felület; új eredeti-Picasa képkocka/videó nem készült. A 38.2.81-83 job-239/240/241 mérései korábbi, külön futások, az ottani kép- és JSON-fájlok e munkamenetben nem álltak rendelkezésre, ezért újra nem elemeztem őket.

**Utólagos kiegészítés.** A fenti állítás a 2026-11-04-i munkamenet állapota. A job-373 eredeti felvételének 2026-11-05-i képkockamérése a 38.2.85-ben szerepel.

**A qshow belépési és animációindító útja.** A célzott, helyi PE-diszasszemblálás a `0x005e8a70` Időrend-építőben a `0x008037e0` hívásáig követhető; a `0x008037e0` egyik hívása a `0x007fda00`, amely az érvényességi jelzők ellenőrzése után QPC-időt kér, a `[this+0x430]` mezőbe írja, majd `0x00802230(this, 1)` hívással frissíti az animációs állapotot. A belépési útban ezután több állapotbájt írása következik. Ez az út az Időrendből elérhető animációindítást és a QPC-minta rögzítését bizonyítja; önmagában nem adja meg a teljes képkocka-idősort, a látható animáció hosszát, a rétegek sorrendjét vagy a képkockák és a `+0x388` tömb elemei közötti megfeleltetést.

**A `0x007fda00` állapot-előfeltételei és írásai, helyi újraolvasás.** Az utasítások szerint a rutin csak akkor folytatódik, ha a `[esi+0x2d8]` bájt és a `[esi+0x538]` dword nem nulla (`0x007fda03-0x007fda13`). A negatív `[esi+0x3f4]` értéket nullára írja (`0x007fda15-0x007fda1e`), meghívja a `0x0097e510(0)` segédet, beállítja a `+0x3be` jelzőt, a `0xc40298` indirekt függvényhívással lekéri QPC-t és az eredményt a `+0x430` qword-be írja; ezután `0x00802230`-at hívja (`0x007fda28-0x007fda4f`). Visszatérés előtt a `+0x3ba` és `+0x3bb` jelzőt törli, a `+0x3b8` és `+0x3b9` jelzőt beállítja (`0x007fda54-0x007fda69`). A külön meglévő Ghidra-C-kimenet ugyanilyen ágakat, QPC-hívást, mezőírásokat és hívási sorrendet ad. Ez a rutin feltételhez kötött állapotfrissítését erősíti meg; a QPC-értékből és az egyszeri hívásból **nem** következik a teljes látható animáció időtartama vagy időgörbéje.

| Állítás / érték | Forrás |
|---|---|
| Az Időrend-építő címe és a `CThumbUI::MakeTimeline` / `Preparing timeline...` sztringek hivatkozása. | bináris (`0x005e8a70`) |
| A qshow belépési hívásút `0x005e8a70` → `0x008037e0` → `0x007fda00` → `0x00802230`. | bináris (`0x005e8a70`, `0x008037e0`, `0x007fda00`, `0x00802230`) |
| A `[this+0x430]` QPC-időírás és az `0x00802230(this, 1)` animációfrissítő-hívás. | bináris (`0x007fda00`; híváshely `0x007fda4f`) |
| A `0x007fda00` két belépési feltétele, a `+0x3f4` negatívérték-nullázása, a QPC-minta és a `+0x3be`, `+0x3ba`, `+0x3bb`, `+0x3b8`, `+0x3b9` állapotjelző-írásai. | bináris (`0x007fda03-0x007fda69`); függetlenül egyező meglévő Ghidra-kimenet: `2026-10-17-idorend-film-sav.txt`, `0x007fda00` |
| A futó qshow `+0x50c` tokenje; a `+0x388`/`+0x38c` tömb elemei és képrekordjai; az összes kártya forráshalmaza és képszáma. | NINCS MEG |
| A teljes látható animáció-időtartam és képkockáról képkockára a transzformáció/réteg megfeleltetése. | NINCS MEG |
| A jelenlegi PicasaPy-forrásban a mappák és nem üres albumok csoportosítása, legkorábbi felvételi dátum szerinti rendezése, valamint a kártyához átadott legfeljebb négy bélyegkép. | mérés (forrásleolvasás: `src/picasapy/app/timeline_controller.py:151-275,278-327`; nem futtatott program-mérés) |
| A jelenlegi PicasaPy-forrásban nyitáskor választott nulla index; Left/Right út; a 2000 ms-os billentyűátmenet, 4000 ms-os csúszkaátmenet és 16 ms-os QML-timer. | mérés (forrásleolvasás: `src/picasapy/app/qml/PicasaPy/TimelineView.qml:62-124,154-204,168-182`; nem futtatott program-mérés) |
| A job-217 eredeti képkocka fekete teljes képernyőt, középre tett panelt, név/dátumot, görbét, bélyegköteget, vezérlősávot és dátumcsúszkát mutatott; a pontos panelhatár ebből a munkamenetből NINCS MEG. A PicasaPy-forrás teljes képernyős, keret nélküli ablakot és rögzített 600×480-as panelt rajzol, benne kártya-, vezérlő- és csúszkaelemekkel. | mérés (eredeti: a 38.2.17-ben leírt job-217 képkocka; jelenlegi forrás: `TimelineView.qml:9-19`, `TimelinePanel.qml:5-12,395-431,466-520`; ez nem e munkamenetben készült eredeti videó vagy PicasaPy-programmérés) |
| A jelenlegi PicasaPy-forrásban Space a kiválasztott gyűjtemény diavetítését kéri, Escape a nézetet zárja. | mérés (forrásleolvasás: `TimelineView.qml:92-99,191-204`; nem futtatott program-mérés) |
| Az eredeti Időrend teljes videója vagy azonos futásból származó teljes képkockasora. | NINCS MEG |

**A két független út.** A út: a helyi Picasa3 PE célzott Capstone-utasításszintű olvasata végigköveti a `0x007fda00` két belépési feltételét, a `+0x3f4` nullázását, a QPC-írást, az állapotjelzőket és az `0x00802230` hívását. B út: a már létező, külön Ghidra-feldolgozás (`2026-10-17-idorend-film-sav.txt`, `2026-10-21-koteg-1021f.txt`, `2026-10-24-2026-10-24-idorend.txt`) ugyanezeket az ágakat, mezőírásokat, hívottakat és híváshelyet adja. A két út egyezik, ezért ez a szűk rutinleírás **megerősített**; a teljes Időrend-viselkedés és a felületi animáció ettől még **nyitott**.

**Cáfoló kísérlet és annak ellenőrzése.** A cáfolandó hipotézis az volt, hogy `0x007fda00` kizárólag az Időrend animációját indítja. Az index `xrefs` táblájának pozitív hívólistája és a `2026-10-17-idorend-film-sav.txt` Ghidra-hívólistája a qshow belépő `0x008037e0` mellett további hívókat is mutat (`0x00802630`, `0x008032e0`, `0x007fde80`); így a kizárólagossági hipotézis megdőlt. A cáfoló adatot az utasításszintű bejárással ugyanazzal a mércével ellenőriztem: a `0x007fde80`, `0x00802630`, `0x008032e0` és `0x008037e0` függvényekben rendre a `0x007fe158`, `0x00802773`, `0x00803522`, `0x008039e7` címen `call 0x7fda00` áll. Ez a közvetlenhívás-listát megerősíti; a rutin többi hívásának futásidejű szerepét nem állítom.

**Összevetés a jelenlegi PicasaPy-forrással.** A korábbi eredeti-futás megfigyeléseit a 38.2.81-83 szakaszok tartalmazzák, ezek egyedi tesztfutásokra érvényesek.

| Eredeti | Nálunk (2026-11-04-i forrásállapot) | Teendő |
|---|---|---|
| A job-239-ben a négy ismert fixture-mappa `2009_majus` → `2014_november` → `2019_marcius` → `2021_eltero_fajlido` sorrendben, utána `PicasaTeszt`, majd `Recently Updated` csoportként látszott; ez a képernyőn látott sorrend, nem a teljes qshow-forráshalmaz. A statikus belépési út `0x005e8a70` → `0x008037e0` → `0x007fda00` → `0x00802230`. | A controller minden nem rejtett fotót és minden nem üres albumot a csoportosításhoz vesz; a mappakártya dátuma a benne levő ismert EXIF `taken_at` értékek minimuma, a csoportokat dátum, név és azonosító rendezi. | Az ismert fixture-t ugyanazon Picasa-futásban újra kell mérni képkocka/videó felvétellel és teljes katalógus-adattal; a jelenlegi mintákból nem állapítható meg minden album-, mappa- és különleges csoport tagsága vagy az eredeti dátumkulcs. |
| A job-217 képkockán fekete teljes képernyőn középre igazított panel, szürke görbe, gyűjteménynév/dátum, bélyegköteg, vezérlősáv és dátumcsúszka látszik; a panel egzakt pixelhatára ebből a körből NINCS MEG. | A QML keret nélküli teljes képernyős ablakot, rögzített 600×480 panelt, kártyákat, gombokat és csúszkát ír le. | A felület geometriai és réteg-összevetéséhez az eredeti felvétel képkockáit azonos felbontású PicasaPy-felvétellel kell összevetni; a régi képleírás nem pótolja a pontos panel- és rétegkoordinátákat. |
| A job-239 képein mappanév és hónap/év felirat, valamint egymásra helyezett fotókártyák látszanak; a 2021-es kontroll EXIF-dátuma 2021, fájlideje 2023, a felirat 2021. | A controller címkét a legkorábbi EXIF-dátumból készíti, darabszámot ad át, és legfeljebb négy fotó-bélyegképet tesz a QML-kártya modelljébe. | A teljes eredeti kártya tartalmát és a rekordok sorrendjét a futó qshow adatmezőivel kell képekhez kötni; a korábbi felirat önmagában nem bizonyítja, hogy az eredeti közvetlenül EXIF-ből olvas. |
| A korábbi képsor Right/Escape hatást mutatott; a Space a job-240-ben diavetítési felületre lépett. A `0x007fda00` QPC-mintát rögzít, de a teljes felületi átmenet-idő nincs mérve. | A QML Left/Right léptet, Space a kiválasztott csoport diavetítését indítja, Escape zár; a forrásban megadott animációs idő nem eredeti-Picasa mérés. | Videó/képkockasor kell a teljes vezérlőpróbához: Right/Left, slider húzás és pontválasztás, Space, Escape, fókusz és visszatérő kép/gyűjtemény-index. Az autoplay valós periódusát külön, időbélyegzett futásban kell megmérni. |

**A #6532 „Kész, ha” pontjai.** (1) ⛔ Eredeti videó vagy egyetlen futásból teljes képkockasor nem készült; a helyi Colab-segéd dokumentált kimenete képernyőkép/állapotadat, a feladatküldés GH API-t használ, amit ez a munkamenet nem hívhatott. (2) ⛔ A bináris belépő/animációindító hívásút megerősített, de az elrendezés, teljes pálya, időzítés, minden animációs képkocka, kártyaadat és sorrend, valamennyi vezérlőhatás és teljes forráshalmaz nincs végig visszafejtve. (3) ⛔ A PicasaPy-forrással részleges összevetés készült; a nyitott eredeti adat miatt nem állítható elő teljes „eredeti / nálunk / teendő” eltéréslista. (4) ⛔ A megvalósítási jegy nincs megnyitva; csak a qshow belépési és animációfrissítő címek igazoltak, ezért a jelenlegi bizonyítékból még nem indokolt konkrét paritás-javító kódlista. A kódjegy pontos követelményeit csak az eredeti videó és az alább megadott futásidejű adatok után lehet becslés nélkül megírni.

**Nyitott; megszerzésének pontos útja.** Az eredeti futáshoz szükséges egy elérhető Colab/Wine végrehajtó és olyan közvetlen kimeneti csatorna, amely videót vagy azonos, időbélyeges futásból származó képkockasort ad át GitHub-hívás nélkül. Ismert mintakatalóguson kell rögzíteni az Időrendbe lépést, minden `Right`/`Left`-et, mappa- és albumváltást, a csúszka húzását és pontválasztását, a Space/diavetítés/Escape utakat, majd a visszatérő kijelölt képet és gyűjteményt. Ugyanebben vagy elkülönített diagnosztikai futásban olvasandó ki a qshow `+0x50c`, `+0x2f8`, `+0x388` és `+0x38c` állapota, valamint a token → `CSlice+0x64` → képrekord-lánc. A képkockák időbélyegeit és a bináris transzformációs mezőket együtt kell rögzíteni, hogy az időgörbe és rétegrajzolás ne képi benyomásból legyen kikövetkeztetve. A meglévő címekhez új Ghidra-kör nem szükséges; a fennmaradó kérdések futásidejű bizonyítékot igényelnek.

**Új kutatási jegyjavaslat.** Nincs; a videó és futásidejű adatfelvétel a #6532 jelen feladatán belüli blokkoló nyitott pont. A bizonyított eltérésekről fejlesztési jegy csak a mérés után írható pontosan.

#### 38.2.85 A job-373 eredeti videójának képkockamérése (#6532, 2026-11-05)

**Történeti státusz:** a szakasz alábbi elfogadási mérlege 2026-11-05-én készült; a 2026-11-10-i, részben lezárt állapot a 38.2.105-ben található.

**Forrás és verzió.** A forrás a `picasa-colab-jobs #373` felvétel, `~/.local/share/picasapy-meroadat/idorend/idorend-job373.mp4`; a felvétel kísérőadata szerint eredeti Picasa 3.9, 1280×1024, 15 kép/másodperc és 100 másodperc. A dekóder 1500 képkockát olvasott be. A helyi `Picasa3.exe` fájlba írt verziószáma `3.9.141.259` / `3.9.141`. A fájl SHA-256 értéke `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`, ez karakterre egyezik a bináris index `meta.binary_sha256` értékével. Ez a helyi exe és az index azonosságát igazolja; a videó kísérőadata a 3.9-es kiadási ágat nevezi meg, de a futó Colab-példány programfájljának verziószáma és hash-e nem szerepel a videóban, ezért a futó és helyi bináris azonossága **NINCS MEG**. A `copy_Picasa_3_7` könyvtárnév önmagában nem verzióbizonyíték; a helyi exe tényleges PE-verziója 3.9.141.259, a korábbi 38.2.61-ben vizsgált `bezier.txt` eszközfájl-verziója viszont **NINCS MEG**. A következő címek a helyi, 3.9.141.259-es programfájlra vonatkoznak.

Az alábbi videóidők a képkockasorszám osztva a felvétel 15 kép/másodperces sebességével. A koordináták a 1280×1024-es képen, bal felső origóval értendők. A képkockás mérés nem tartalmazza a billentyűesemény tényleges időbélyegét, ezért a változás első és utolsó látható képkockáját rögzíti, nem a belső időzítő kezdőpontját.

**Nyitás.** Az 5.000 másodperces 75. képkocka még a könyvtárnézet. Az 5.067 másodperces 76. képkockán már a teljes Időrend-panel látszik. A 76-91. képkockák mindegyikén, 20-as és 30-as szürkeérték-küszöbnél egyaránt `x=340, y=272, szélesség=600, magasság=480` panelhatár mérhető. A panel külső kerete nem méreteződik és nem tolódik el. A belső rajz, a feliratok, a pontív, a kártyalapok és a vezérlősáv viszont az első látható képkockától a 90. képkockáig folyamatosan változik. A 91. képkocka 6.067 másodpercnél az első stabil ellenőrzött képkocka; a 90-ről 91-re váltás panelbeli szürkeérték-különbségének maximuma 9, és nincs 10 fölötti pixelkülönbség. A látható nyitó átmenet így 76. és 91. képkocka között 15 képkocka-idő, azaz 1.000 másodperc.

Az átmenet nem a teljes panel méretezése. A rögzített panelen belül a sötét, ferde csíkozású mező, a nagy bal oldali képfelirat, a jobb felső gyűjteménynév és dátum, a pontok, a színes lapok és az alsó vezérlők fokozatosan rajzolódnak ki, illetve változtatják a helyüket. Az elemrétegenkénti pontos áttűnési görbe, a pozíciógörbe és a natív időzítőérték **NINCS MEG**.

**Nyugalmi elrendezés.** A 10.000 másodperces 150. képkocka a `2009_majus / May 2009` állapotot mutatja. A fekete képernyőn középen álló 600×480-as panelen belül nagy, sötét, ferde csíkos ovális mező, halvány külső ív és az íven felfelé futó sötét pontsor látszik. A jobb felső felirat `2009_majus`, alatta `May 2009`; a bal alsó nagy felirat `2009_majus`, alatta a képen olvasható `2009-05-14 10:00`. Az alsó sávban kilépés, balra léptetés, diavetítés és jobbra léptetés vezérlő látszik. Alatta vízszintes dátumvonal, pontok, gömb alakú csúszkajelző, valamint `May 2009` és `November 2026` szélső dátumfelirat látható. A három színes kártyalap mért téglalapja a 150. képkockán: piros `(704,604,70,52)`, kék `(795,592,76,66)`, zöld `(876,568,64,72)`. A téglalapok koordinátája és színe képmérés; a lapok belső képtartalma és qshow-rekordja közötti megfeleltetés **NINCS MEG**.

**Jobbra léptetés és a látható pálya.** Az első váltás előtt a színes lapok helye a 225. képkockán, 15.000 másodpercnél még azonos a nyugalmi helyükkel. Az első észlelt változás a 226. képkockán, 15.067 másodpercnél jelenik meg. A színes téglalapok képkockánként követett bal felső pontja:

| Állapot | Piros | Kék | Zöld | Sárga | Forrás |
|---|---:|---:|---:|---:|---|
| Első váltás előtt, 15.000 mp, 225. képkocka | `(704,604)` | `(795,592)` | `(876,568)` | nincs látható komponens | mérés: picasa-colab-jobs #373 videó, 15.000 mp |
| Első váltás után, 16.467 mp, 247. képkocka | `(608,592)` | `(698,594)` | `(796,584)` | `(880,578)` | mérés: picasa-colab-jobs #373 videó, 16.467 mp |
| Második váltás előtt, 22.867 mp, 343. képkocka | `(608,592)` | `(700,594)` | `(796,586)` | `(880,578)` | mérés: picasa-colab-jobs #373 videó, 22.867 mp |
| Második váltás után, 24.400 mp, 366. képkocka | `(526,570)` | `(604,584)` | `(700,590)` | `(800,596)` | mérés: picasa-colab-jobs #373 videó, 24.400 mp |

Az origók szín alapján elkülönített képpontcsoportok befoglaló dobozaiból származnak; a videó tömörítése miatt a csoportok széle és mért mérete képkockánként változhat. A táblázat a színes lapok látható pixelhelyét rögzíti, nem állítja, hogy minden lap az éppen feliratozott gyűjtemény egy fotója.

A piros, kék és zöld lapok nem egy merev csoportként mozognak: az első váltásban eltérő vízszintes és függőleges elmozdulást mutatnak, és a sárga lap jobb felől láthatóvá válik. A második váltásban mind a négy lap balra halad, eltérő függőleges elmozdulással. Az első váltás képen mérhető változása a 226. képkockán indul és a lapok helye a 247. képkockára áll be; a második a 344. képkockán indul és a 366. képkockára áll be. Ez a videón látható 1.400, illetve 1.467 másodperces változási időablak. A köztes képkockák vizsgálatából sem következik egyetlen közös pályaegyenlet vagy időgörbe; az egyes rétegek és a bináris transzformációs rekordok megfeleltetése **NINCS MEG**.

**Space, Escape és a második Ctrl+5.** A 30.800 másodperces 462. képkockán a Space után elindul a `2019_marcius` gyűjtemény diavetítése. Az első lap szövege `2019_marcius 1/7 2019-03-08 09:15`; zöld képmező és alsó diavetítés-vezérlősáv látszik. A 49.333 másodperces 740. képkockán az Escape után a Picasa könyvtárnézet látszik, nem az Időrend. Ez az eredmény összhangban van azzal, hogy a Space a kiválasztott gyűjtemény diavetítésébe lép, az Escape pedig bezárja az Időrend bemutatóját. A videó nem mér külön diaváltást, ezért az automatikus lapozási idő **NINCS MEG**.

A későbbi `Left`, `Escape` és `Ctrl+5` eseménysor után az Időrend a 66.600, 66.667, 66.733 és 67.333 másodperces képkockák egyikén sem jelenik meg újra. Az 1000. képkocka és az előző képkocka szürkeérték-különbségének maximuma 8; 12 fölötti eltérés nincs, az 1000. és 1001. képkocka szürke képe azonos. A látható kezelőfelület nem változik. A 66.667 másodpercnél említett kismértékű képi eltérés nem tartalmaz azonosítható Időrend-panelt vagy más vezérlőállapotot. A felvétel nem rögzíti, hogy a második `Ctrl+5` billentyűesemény eljutott-e az alkalmazáshoz, ezért az ok **NINCS MEG**.

**Összevetés a binárissal.** A helyi `Picasa3.exe` verziószáma `3.9.141.259`, termékverziója `3.9.141`, SHA-256 értéke egyezik a bináris indexével; a videó kísérőadata Picasa 3.9-et nevez meg. A futó Colab-példány pontos programfájl-azonossága ettől függetlenül **NINCS MEG**.

| Állítás | Forrás |
|---|---|
| A qshow belépési állapotfrissítője a QPC-értéket a `[this+0x430]` mezőbe írja, majd `0x00802230(this,1)` hívást végez. | bináris (`0x007fda00`, híváshely `0x007fda4f`); a már meglévő Ghidra-kimenet is egyezik (`2026-10-17-idorend-film-sav.txt`, `0x007fda00`) |
| A `0x00802230` QPC-mintát is olvas (`0x008025b9`) és a `[this+0x520]` mezőbe menti (`0x008025cf`). | bináris (`0x00802230`) |
| A `0x00802230` az új és előző eltolás mezőit kezeli (`+0x400/+0x404`, `+0x408/+0x40c`); a `0x007fff30` ezekből transzformációt és átlátszóságot számol, a `0x007fbab0` görbeértéket ad. | bináris (`0x00802230`, `0x007fff30`, `0x007fbab0`; 38.2.61-62) |
| A videó szerinti nyitás képernyőbeli ideje 1.000 másodperc; a két kártyaváltás változási ablaka 1.400 és 1.467 másodperc. | mérés: picasa-colab-jobs #373 videó, 5.067-6.067 mp, 15.067-16.467 mp, 22.933-24.400 mp |
| A nyílág a `0x00cf3a48` címen levő `2.0f` értéket adja a `0x007fd0c0` hívásnak. Ez a függvényargumentum, nem bizonyított animációs időtartam. | bináris (`0x008011b0`, `0x00cf3a48`, `0x007fd0c0`; 38.2.63 és 38.2.66) |
| A QPC-minta vagy a `0x00802230` önmagában megadná a most mért látható nyitó- és lapváltási időt, illetve a színes lapok képernyőpályáját. | NINCS MEG |

Ezért a mért látható időablakokat nem azonosítom a `2.0f` bináris értékkel. Az 1.400 és 1.467 másodperces videómérés nem egyenlő 2.0 másodperccel, de a binárisból sem következik, hogy a `2.0f` másodpercet jelentene. A `0x007fda00` QPC-mintát rögzít és az animációs állapotfrissítőt hívja; a videó és a statikus kód között a belső időzítő és a látható kártyarétegek megfeleltetése **NINCS MEG**.

**Összevetés a PicasaPy-forrással.** A sorok forrásai a munkafában olvasott QML/Python-kódok, nem futtatott PicasaPy-mérések.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A panel mért határa `340,272`, mérete `600×480`; nyitáskor a belseje változik, miközben a keret a mért képkockákon rögzített. | A `TimelineView.qml` teljes képernyős, fekete, keret nélküli ablakot és rögzített 600×480 panelt deklarál; a panel középre van horgonyozva. A `visible` változás fókuszt állít és visszaállítja a kártyát, de nem indít nyitó animációt. | A panel mérete és középre helyezése egyezik. A videóban látszó belső nyitó átmenetet implementálni kell, miután annak rétegeit a bináris mezőkhöz kötöttük. A helyi QML megfelelő része: `TimelineView.qml:6-19,101-109,154-165`. |
| A sötét mezőn ferde csíkozás, halvány külső ív, pontív, nagy bal oldali képfelirat és a jobb felső gyűjteménynév/dátum látszik. | A `TimelinePanel.qml` Canvas-e egyszínű sötét mezőt, egy halvány Bézier-ívet és pontokat fest; a gyűjteménynév és dátum a panel jobb felső részére kerül. Ebben a fájlban nincs a videóban látható ismétlődő ferde csíkozás, és nincs nagy bal oldali képfelirat. | A bal oldali képfelirat és a ferde mintázat megjelenítését hozzá kell adni; pontos tartalmuk, rétegsorrendjük és címük a binárisban **NINCS MEG**. Forrás: `TimelinePanel.qml:60-138,335-368`. |
| Nyugalmi állapotban három különálló színes lap látszik; a váltás után négy, egymástól különböző helyen álló lap látszik. Mindegyik külön elmozdul, a második váltásban mind balra halad. | A jelenlegi kártyaköteg egy Bézier-paramétert használ a csoport képeihez; az egymás melletti lapok csak indexenként 4 px vízszintes és 3 px függőleges eltérést kapnak. A nyíl a `TimelineView.qml` szerint 2000 ms-os átmenetet kér. | A négy lap külön pályáját és a nyitott, valamint léptetési időbeli lefutást a mért videó és a bináris adatmezők alapján kell megvalósítani. A jelenlegi köteg geometriája nem egyezik a videóban mért különálló lapokkal. Forrás: `TimelinePanel.qml:147-177,215-237,273-301`; `TimelineView.qml:62-90,168-183`. |
| A felvételben a látható lapváltás 1.400, illetve 1.467 másodperces ablakot foglal el; Right után `2014_november`, majd `2019_marcius` látszik. | A vezérlő `Right`/`Left`-re lép, az első gyűjteménnyel nyit, a gyűjteményeket legkorábbi `taken_at` dátum, név és azonosító szerint rendezi. A 2000 ms a forrásban kért idő, nem futásidejű mérés. | A csoportlista teljes forráshalmazát és eredeti dátumkulcsát még ki kell nyerni. A látható 2.0f bináris argumentum nem használható másodpercként. Forrás: `timeline_controller.py:151-180,182-276,278-327`; `TimelineView.qml:86-90`. |
| Space után a `2019_marcius` gyűjtemény `1/7` első lapja indul; Escape után a fő könyvtárnézet marad. A későbbi Ctrl+5 nem nyitja újra láthatóan az Időrend panelt. | A Space a kiválasztott gyűjtemény modelljét kéri, a timeline bezárul, majd a diavetítés `start(0)`-val indul. A Ctrl+5 parancs aktív, ha nincs szövegfókuszban, nézőben vagy diavetítésben. Az Escape utáni visszatérő kiválasztás és az újranyitás nem futtatott PicasaPy-adat. | Ugyanazzal a katalógussal futás közben ellenőrizni kell az első diaképet, Escape utáni nézetet és kijelölést, majd az újabb Ctrl+5-öt. A videó nem bizonyítja, hogy a második billentyűesemény eljutott az eredeti programhoz. Forrás: `TimelineView.qml:92-99,191-204`; `MainTimeline.qml:53-88`; `MainKeyboardShortcuts.qml:366-370`. |

**A két független út.** A út: a job-373 videó képpontjai, szövegei és színes lapjainak képkockánkénti mérése. B út: a helyi PicasaPy QML/Python-forrás és a helyi Picasa 3.9.141.259 PE utasítás/Ghidra leletei. A két út a panel 600×480-as méretén egyezik, mert a videó pixelhatára és a középre horgonyzott QML-méret ugyanaz. A Right/Space/Escape események látható hatása összhangban áll a helyi bináris korábban dokumentált billentyűútjaival és az Időrendből indított diavetítés útjával. Ez nem erősíti meg a belső rajzrétegek, a pontos időbeli lefutás vagy a `0x00802230` mezőinek képernyőelemhez rendelését. A teljes viselkedési következtetés ezért **feltételes**; csak a panel méret-paritása **megerősített**.

**Cáfoló kísérlet és ellenőrzése.** A cáfolandó feltevés az volt, hogy nyitáskor az egész panel méreteződik vagy eltolódik. A teljes 76-91. képkocka-sorozaton két külön szürkeérték-küszöbbel ellenőriztem a panelhatárt; mindkét küszöb minden képkockán ugyanazt a `340,272,600,480` értéket adta. A 90-91. képkocka belső képkülönbsége ettől függetlenül a 9-es maximumra esik, vagyis a tartalom a rögzített panelen belül áll be. A küszöbváltás nem változtatja meg a cáfolatot: a panel egészének méretezése vagy eltolása nem látszik. Ez nem cáfolja a belső rétegek áttűnését vagy külön mozgását.

**A #6532 „Kész, ha” pontjai.** (1) ✅ Van eredeti videó, és a teljes 1500 képkocka dekódolható; a vizsgált menetet és a képkocka-időket ez a szakasz rögzíti. (2) ⛔ A képernyőn látható nyitó/mozgató rétegek és a qshow adatmezői nincsenek teljesen összekötve; a forráslista, teljes kártyasorrend és natív időzítőérték **NINCS MEG**. (3) ⛔ Az eredeti/nálunk/teendő táblázat elkészült, de teljes PicasaPy-futásmérés és minden csoport tartalmának megfeleltetése hiányzik. (4) ⛔ Megvalósítási jegy nincs nyitva, mert ebben a munkamenetben nincs GitHub-hozzáférés; a bizonyított eltérések fejlesztői átadószövege a munkajelentésben szerepel.

**Nyitott és megszerzésének útja.** A videóhoz használt futó exe pontos verziója/hash-e; a színes lapok, nagy bal oldali felirat, ferde háttér és pontok qshow-tokenhez, `+0x388`/`+0x38c` elemekhez és képrekordokhoz kötése; a nyitás és két léptetés natív időbélyege és belső időbeli lefutási görbéje; a második Ctrl+5 esemény eredeti program általi fogadása; a teljes eredeti gyűjteményforrás és minden kártya képszáma; a diavetítés automatikus lapozási ideje. Megszerzésükhöz a Picasa 3.9 folyamatban ugyanazon futás alatt kell rögzíteni a billentyűesemények időbélyegét, képkockát és a fenti qshow-adatmezők pillanatnyi értékét, majd a token → `CSlice+0x64` → képrekord láncot. A `0x007fda00` és `0x00802230` címhez már van meglévő Ghidra-kimenet, ezért ugyanarra a kérdésre új dekompilációs kört nem kérek; az itt fennmaradó képernyőelem-hozzárendeléshez futásidejű adat hiányzik.

**Új kutatási jegyjavaslat.** Nincs. A fennmaradó kérdések a #6532 teljes visszafejtési hatókörében maradnak.

#### 38.2.86 A látható rétegek bináris idő- és rajzútja (#6532, 2026-11-05)

**Hatókör és futó programfájl.** A 38.2.85-ben kimért job-373 felvétel jeleneteit vetettem össze a helyi `Picasa3.exe`-vel. A PE-verzió `3.9.141.259`, a SHA-256 egyezik a bináris indexével, de a videóban futó programfájl azonos hash-e nincs rögzítve. Ezért a bináris-állítások a helyi programfájlra vonatkoznak; a videós egyezés nem bizonyítja a felhős példány pontos programfájl-azonosságát.

**A nyitás egy másodperces rajzága.** A `0x007fda00` QueryPerformanceCounter-értéket ír a qshow `[this+0x430]` mezőjébe (`0x007fda3d`-`0x007fda49`), majd a `0x00802230` állapotfrissítőt hívja (`0x007fda4f`). A `0x00800a30` rajzoló az eltelt időt a `0x009a51b0` függvénnyel számítja a `[this+0x430]` mezőből. Ezt az értéket 0 és a PE `0x00c79c88` címén tárolt f32 `1.0` közé korlátozza, majd a PE `0x00cf39d8` címén tárolt f64 `256.0` értékkel szorozza, egészre kerekíti, és a `0x007ffc90` rajzolónak adja (`0x00800cc9`-`0x00800d46`, a párhuzamos festési ágban `0x00800f1d`-`0x00801003`). A kód tehát egy másodperces, QPC-másodpercben számolt felső korlátot használ a pont- és felirat-rajzolási út progresszértékéhez. Ez nem animátorrekordban tárolt időtartammező.

A `0x007ffc90` a qshow `+0x388` dupla pontosságú tömbjéből számol pontpozíciókat, és meghívja a `0x007fee70` címkefestő függvényt. Utóbbi a qshow `+0x510` kiválasztott dátumértékéből, valamint a `+0x3a8/+0x3ac` rekordvektor dátumaiból szöveget állít elő. A `0x0098c780` `ytDateTime::Format2` függvény string-xrefje a `0x00cd89c4` címen szerepel; a használt formátumszöveg `%s %d` (`0x00c87dd0`). A `0x007fee70` a `HelveticaNeue MediumCond` és `HelveticaNeue Condensed` betűnevekkel hoz létre szövegobjektumokat a `0x00a48e10` híváson át, majd a rajzoló út a `0x009e6df0`-hez jut. Ez a dátum hónap/év felirat útját és a videó 10.000 másodperces képkockáján látható `May 2009` szöveggel való egyezést támasztja alá.

A nyitási időkorlát nem azonosítható a teljes panel áttűnésével. A `0x007ffc90` egy számszerű haladási értéket kap, ponthelyeket és címkéket rajzol; ez a hívás nem kap alfa-paramétert. A kártyákhoz a `0x008001c0` külön hívja a `0x007fff30` transzformációt, amely a korábban dokumentált időfüggő méretet, helyzetet és átlátszóságot adja. A 38.2.85-ben mért, panelen belüli teljes változás egy másodpercig tart, de a `+0x430` út és az összes látható réteg közötti teljes kapcsolat **NINCS MEG**. A bal alsó `2009_majus` mappanév és `2009-05-14 10:00` dátum teljes szövegforrása/formázója szintén **NINCS MEG**.

**Nyíllal indított animátor és a lapváltás mérése.** A qshow billentyűútja a `0x008011b0` vagy `0x00801210` rutinon át jut el a `0x007fd0c0` animátorkészítőhöz. A hívás a qshow `+0x2f8` objektumának `+0x30` mezőjét és a `0x00cf3a48` cím első f32 értékét, `2.0`, adja át; a `0x007fd0c0` ezt a második paraméterként kapja. A függvény a QPC-értéket másodpercre váltó `0x009a5210`-től induló időpontot olvassa, hozzáadja a paramétert, majd az animátor kezdő- és végidejével új rekordot fűz be a `0x009e6010`-en át. A rekordkiértékelő `0x009e5e70` a kezdő- és végidő közti eltelt időből normalizált értéket képez, majd a rekord görbehívását használja. A `2.0` ebben az útban tehát két másodperces belső animátorrekord-időtartam, nem sebesség.

A kártyák kirajzolásának másik, már dokumentált útja a `0x007fc010`: a qshow `+0x2f8` objektumból a `+0x3ac` rekordvektort járja, rekordonként a `0x007fbab0` görbét hívja, majd a transzformációs adatot a `0x007fa650`-nek adja. A `0x007fbab0` képlete a 38.2.61-ben van megadva: `b0=(1-t)^3`, `b1=3(1-t)^2t`, `b2=3(1-t)t^2`, `b3=t^3`, `D=Σ bi·wi`, `x=(Σbi·xi-0.5)/D+0.5`, `y=(Σbi·yi-0.5)/D+0.5`, `z=1/D`. A `0x007fff30` transzformáció- és alfa-képlete a 38.2.62-ben szerepel. Bár az animátor és a kártyarajzolás ugyanazon `qshow+0x2f8` alapcím környezetében dolgozik, a `+0x30` érték egy adott színes kártya képpontjaihoz rendelése nincs bizonyítva.

A videó látható mozgása az első nyílváltásnál a 226. képkockán indul 15.067 másodpercnél, és a 247. képkockán 16.467 másodpercnél már a megmért véghelyzetet mutatja: a látható változási ablak 1.400 másodperc. A második váltás a 344. képkockán indul 22.933 másodpercnél, a 366. képkockán 24.400 másodpercnél a megmért véghelyzet látszik: a változási ablak 1.467 másodperc. Ezek a 38.2.85-ben rögzített videómérések. A bináris belső időtartama két másodperc, a videó látható mozgása rövidebb. Ez számszerű eltérés; a konkrét animátorrekord és a megmért színes lapok közötti mező-képpont kapcsolat hiánya miatt nem dönthető el, hogy valódi ellentmondásról van-e szó. A különbséget nem magyarázom becsült görbével vagy szabad paraméterrel.

**Háttérkép és ferde csíkozás.** A `0x007fb210` erőforrás-betöltő a `0x00cbd3e8` című `overlays/overlay` szöveget adja a `0x00410fa0` betöltőnek (`0x007fb4aa`-`0x007fb4af`), és az objektumot a qshow `+0x648` mezőhöz köti (`0x007fb4bb`). A erőforráscsomag azonos nevű `layer:overlays/overlay` eleme 640×480 képpontos RGBA-kép; a kicsomagolt forrás átlátszósági értékei 179 és 255 közöttiek. Az ovális sötét felület, halvány külső ív és alsó sáv a 10.000 másodperces videóképkocka paneljének alakjával összhangban áll.

A forráskép ovális mezőjén nincsenek a videón látható ferde csíkok. A `0x007fb210` betöltés közbeni további hívásai (`0x00a42c20`, `0x009dc000`, `0x00425160`) az erőforrás objektummá alakítási útjában vannak; nem igazolják, hogy ezek közül melyik rajzolja a panelre. A csíkozás külön erőforrása vagy ecsete, előállító kódja és végső képernyőrajzoló hívása **NINCS MEG**. A háttérkép-azonosítást ezért csak az ovális keretre és az alsó sávra szűkítem.

**Bizonyíték és bizonyítottsági fok.** A qshow időmezőinek és a két literálnak az utasításszintű olvasata, a QPC-segéd és a rögzített erőforráscímek a helyi, hash-azonos binárisból származnak. A 38.2.61-62 korábbi, a mostani utasításolvasattól külön úton készített Ghidra/QEMU-ellenőrzései megerősítik a görbe- és transzformációképleteket; a hívási gráf és a `ytDateTime::Format2` string-xrefje független támpont a címkéző út besorolásához. A video-frame mérés függetlenül igazolja a látható egy másodperces nyitást, a rövidebb lapmozgásokat és a feliratokat, de nem igazolja a futó programfájl pontos hash-ét vagy a qshow mezőket. **A két belső időmechanizmus (egy másodperces haladási korlát, két másodperces animátorrekord) megerősített. A hozzájuk rendelt teljes vizuális réteg, az alsó dátumfelirat, a csíkozás és a 2.0 másodperc/pixelpálya azonosság feltételes vagy nyitott. A teljes látható rétegek binárisból visszafejtése ezért feltételes.**

**Cáfoló kísérletek.**

1. A `0x00cf3a48` értéket sebességnek vagy koordinátának vélő olvasatot próbáltam cáfolni: a `0x007fd0c0` a QPC-másodpercet olvassa, és a második paramétert a végidőhöz adja, majd a két időből kiértékelhető rekordot hoz létre. A próbát a gépi kód és a `0x009e5e70` kiértékelő útja egyaránt megerősíti: ez az érték az animátorrekord ideje, nem sebessége. Ez önmagában nem bizonyítja, hogy a rekord a videó minden színes lapját vezérli.
2. Azt a jelöltet vizsgáltam, hogy a `overlays/overlay` kép a ferde csíkozás forrása. A erőforráscsomagból kicsomagolt RGBA-kép ovális közepén egyszínű sötét mező van, ismétlődő ferde minta nélkül; a videó 10.000 másodperces képkockáján ugyanott csíkok látszanak. A jelölt erőforrás tehát nem magyarázza a csíkozást; az eredeti minta forrása továbbra is **NINCS MEG**.
3. Azt a feltevést ellenőriztem, hogy az egy másodperces korlát maga a panel átlátszósága. A `0x00800a30` az eltelt másodpercet 256 lépésre alakítja, majd a `0x007ffc90` pont- és dátumfelirat-rajzoló útjának adja; a kártyák külön `0x007fff30` kódja állít elő alfát. Ez nem támasztja alá, hogy a panel egészét egyetlen átlátszósági átmenet rajzolja ki.

**Független utak.** A út: a `0x007fda00`, `0x00800a30`, `0x008011b0`/`0x00801210`, `0x007fd0c0` és `0x009e5e70` eredeti utasításainak olvasata, a QPC-másodpercre váltó segéddel és a PE-literálok kiolvasásával. B út: a meglévő Ghidra-kimenetek (`2026-10-21-idorend-12.txt`, `2026-10-20-idorend-6.txt`), az index közvetlen hívókapcsolatai, a `ytDateTime::Format2` string-xrefje és a `respack.yt` külön tartalmának képi ellenőrzése. A két út egyezik a qshow nyitási időbeli haladásának és a belső két másodperces animátorrekordnak a szerepében; a videó nem köti össze az animátorrekordot az egyes kártyakép-pixelekkel.

| Állítás | Forrás |
|---|---|
| A belépési qshow-út QPC-mintát ír a `+0x430` mezőbe; a rajzoló ezt másodpercben olvassa, `0.0` és `1.0` közé korlátozza, majd `256.0` skálán adja a `0x007ffc90`-nek. | bináris (`0x007fda00`, `0x00800a30`, `0x009a51b0`, `0x00c79c88=1.0f`, `0x00cf39d8=256.0`) |
| A `0x007ffc90` dátumpont-út hívja a `0x007fee70` függvényt; ott `ytDateTime::Format2` (`%s %d`) és a `HelveticaNeue` betűnevek szerepelnek. | bináris (`0x007ffc90`, `0x007fee70`, `0x0098c780`, `0x00cd89c4`, `0x00c87dd0`, `0x00a48e10`, `0x009e6df0`) |
| A nyílág a `0x00cf3a48` címen levő `2.0f` értéket időtartamként adja az animátorrekord-készítőnek; az időalap másodperc. | bináris (`0x008011b0`, `0x00801210`, `0x007fd0c0`, `0x009a5210`, `0x009e6010`, `0x009e5e70`) |
| A kártyarekordok a `0x007fbab0` görbét, majd a `0x007fff30` transzformációt és átlátszósági ágat használják. | bináris (`0x007fc010`, `0x007fbab0`, `0x007fff30`; 38.2.61-62) |
| A `overlays/overlay` qshow `+0x648` mezőjéhez töltődik; a 640×480-as forrás oválist és alsó sávot tartalmaz, de a megfigyelt ferde csíkot nem. | bináris (`0x007fb210`, `0x007fb4aa`-`0x007fb4bb`; `layer:overlays/overlay`) + mérés (kicsomagolt RGBA-payload vizsgálata és video frame 150, 10.000 s) |
| A panel 600×480-as állandó kerete, a látható `May 2009`/`2009_majus`/`2009-05-14 10:00` felirat és a 1.400/1.467 másodperces kártyamozgás. | mérés (picasa-colab-jobs #373, frame 76-91, 150, 226-247, 344-366; 38.2.85) |
| A felhős videóban futó programfájl SHA-256 értéke, a `+0x30` animátormező és az egyes színes lapok pontos pixelei közti kapcsolat, a csíkozás forrása és a bal alsó teljes felirat bináris bemenete. | NINCS MEG |

**A 2. kör elfogadási pontjai.** (1) ⛔ A nyitó rajzág egy másodperces felső korlátja és a pont/felirat útja binárisból megvan; az összes belső réteg, különösen a csíkozás és a bal oldali dátumfelirat nem. (2) ⛔ A `2.0f` két másodperces rekord-időtartama bizonyított, a Bézier- és transzformációs képletek megvannak; az egyes színes lapokhoz kötés és a látható 1.400/1.467 másodperces ablakkal való eltérés feloldása nincs meg. (3) ⛔ Az `overlays/overlay` shell kép megvan; a csík ecsete/erőforrása, a végső rajzolóhívás és a bal alsó felirat mappanév + dátum forrása nyitott. (4) ✅ A fenti bináris állítások címmel, a videóállítások képkockaidővel szerepelnek; a két időadat eltérése kimondott és nincs megbecsülve. (5) ✅ A 38.2.86 leírja a bizonyított fejlesztői kiindulópontokat és azokat a hiányzó kapcsolatokat, amelyek nélkül nem adható teljes vizuális megvalósítási lista.

**Fejlesztőnek átadható, kizárólag binárisból igazolt elemek.**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A qshow nyitó rajzága a `[this+0x430]` QPC-időből `clamp(elapsed_seconds,0,1.0) * 256.0` értéket állít elő, és a `0x007ffc90`-en át rajzol pontokat/címkéket. A videón látható 1.000 másodperc **csak mérés**. | A `TimelineView.qml` rögzített, középre tett 600×480-as panelt deklarál, nyitó animációt nem indít (`TimelineView.qml:6-19,101-109,154-165`). | A bináris időkorlát csak a pont/címkerajzáshoz vehető át. A teljes panel alfa- vagy háttérátmenetére ne terjessze ki: ilyen rétegkapcsolat **NINCS MEG**. A PicasaPy azonos képkockás futásmérése hiányzik. |
| A `0x007fd0c0` a QPC-másodperc mellé két másodperces animátor-végidőt készít; a `0x007fbab0` és `0x007fff30` kártyarekordokhoz görbe-, transzformációs és alfaértékeket ad. A videón mért 1.400 és 1.467 másodperces mozgásablak **csak mérés**. | A PicasaPy nyílkezelője 2000 ms-os átmenetet kér (`TimelineView.qml:62-90`); ez forráskód, nem futásidejű mérés. | A két másodperc a binárisból igazolt belső animátor időtartama. A kártyákhoz való pontos hozzárendelés és a videóméréstől való eltérés oka **NINCS MEG**; a fejlesztő ne kezelje bizonyított 1.4 másodperces mozgásképletként. |
| A `0x007fb210` a 640×480-as `overlays/overlay` erőforrást tölti a qshow `+0x648` mezőjéhez. A 10.000 másodperces képkockán látható ferde csíkozás **csak mérés**. | A `TimelinePanel.qml` egyszínű sötét mezőt és halvány ívet fest; az ismétlődő csíkozás nincs benne (`TimelinePanel.qml:60-138,335-368`). | Az ovális shell és alsó sáv lehetséges erőforrása az `overlays/overlay`. A ferde minta és a végső képernyőre rajzoló hívás **NINCS MEG**. |
| A `ytDateTime::Format2` formátuma `%s %d`; a címkéző út a qshow dátumvektorához jut. A `May 2009` felirat a 10.000 másodperces képkockán **csak mérés**. | A PicasaPy gyűjteménynevet és dátumot a panel jobb felső részére tesz (`TimelinePanel.qml:335-368`); a bal oldali mappanév és teljes dátumfelirat jelenlegi forrása **NINCS MEG**. | A hónap-év megjelenítési út kiindulópontja binárisból ismert. A bal oldali mappanév + teljes dátumfelirat forrása **NINCS MEG**. |

**Nyitott.**

- A 1.000 másodperces progresszút mely belső rétegeket mutatja, és a `0x007fee70` melyik vizuális feliratot rajzolja; a teljes nyitó-képkocka és `+0x430`/rajzobjektum-megfeleltetés.
- A nyílbillentyűvel ütemezett `qshow+0x2f8+0x30` animátorrekord pontos pixelhatása az egyes kártyákra, valamint hogy a 2.000 másodperces belső rekord miért különbözik a videón látható 1.400/1.467 másodperces változási ablaktól. Az időtartam-eltérést további görbeillesztés nélkül nyitva hagyom.
- Az `overlays/overlay` végső képernyőrajzoló hívása, a ferde háttérminta erőforrása/ecsete és létrehozója.
- A `2009_majus` mappanév forrása, valamint a `2009-05-14 10:00` felirat fotó-/mappadátumának mezője és pontos formázófüggvénye.
- A felhős job-373 felvételben futó Picasa programfájl hash-e.
- A `0x007fee70` kiválasztott-indexű szövegének és hónap/év értékének adatútja a helyi virtuális tábla és az utasítások olvasatával tisztázva (§38.2.88). A teljes `YYYY-MM-DD hh:mm` felirat forrása továbbra is nyitott.

**Új kutatási jegyjavaslat.** Nincs. A nyitott címke-, csíkozás- és pixelkapcsolatok a #6532 feladatának részei; megvalósítást csak azután lehet teljes specifikációként átadni, hogy ezeket binárisból vagy pontos futásméréssel azonosítottuk.

#### 38.2.87 Mit csinál a nyitó egy másodperc: két képréteg beúsztatása legfeljebb 39%-ig (#6532, 2026-11-05)

**Kérdés.** A 38.2.86 szerint a `0x00800a30` a nyitás óta eltelt időből `p = kerekítés(clamp(t, 0, 1,0) x 256)` értéket ad a `0x007ffc90`-nek, de nyitva maradt, mire használja a `0x007ffc90` ezt az értéket.

**Utasításszintű olvasat (helyi, hash-azonos programfájl, capstone).**

| hely | mit csinál |
|---|---|
| `0x007ffc95` | `ebp = p` (a verem első paramétere). |
| `0x007ffca2`-`0x007ffca5` | `0x007fee70(this, cél, p)`: a feliratfestő ugyanazt a `p`-t kapja. |
| `0x007ffcb2`-`0x007ffcd0` | `ebx = (p x 0x64) >> 8`, azaz `p x 100 / 256`: `p = 256` esetén 100. |
| `0x007ffcc9`-`0x007ffcd8` | `0x009ab690(cél, ebx, &this[+0x620], téglalap = -1)`. |
| `0x007ffcf7`-`0x007ffd00` | ugyanez a `this[+0x5f8]` képpel, ugyanazzal az `ebx`-szel. |
| `0x007ffd05`-`0x007ffd0e` | `0x007fd180(&this[+0x2f8], cél, p)`: a kártyák animátora is megkapja a `p`-t. |
| `0x009ab72e`-`0x009ab798` | a `0x009ab690` MMX-ága: a második paramétert minden színcsatornára kiterjeszti, a forrásképpontot és a forrás alfáját `x param >> 8` szorzással gyengíti, majd előszorzott alfával a célra keveri (`cél x (255 - forrásalfa x param >> 8) >> 8 + forrás x param >> 8`). A második paraméter tehát **átlátszósági szorzó 256-os skálán**. |

**Következtetés.** A nyitás első másodpercében a `+0x620` és a `+0x5f8` kép átlátszósága lineárisan nő 0-ról `100/256`-ra, azaz **legfeljebb kb. 39%-ra**, és utána ott marad (a `p` felső korlátja 256). Ez bizonyított; a két kép teljes fedéssel soha nem rajzolódik ezen az úton.

**Nyitott.** Hogy mi van a `+0x620` és a `+0x5f8` képben, az nincs meg: az erőforrás-betöltő (`0x007fb210`) ezt a két mezőt nem tölti (a `left`, `right`, `mouse`, `rollovermouse`, `exit`, `timeline`, `timelinedot`, `sliderthumb`, `startbutton` és `overlay` erőforrás a `+0x530`, `+0x558`, `+0x5a8`, `+0x5d0`, `+0x580`, `+0x6c0`, `+0x6e8`, `+0x710`, `+0x738`, `+0x648` mezőbe kerül), és a `0x007f0000`-`0x00808000` tartományban rajtuk kívül csak a konstruktor (`0x007fa7f0`) és a felszabadító (`0x007fb5a0`) nyúl hozzájuk. A kitöltőjük tehát más úton (közvetett mutatóval vagy más tartománybeli függvényből) írja őket. A `p` a `0x007fd180`-ban rekordonként az átlátszósági értéket skálázza; a `0x007fee70` feliratútjában szín-/rajzolási argumentumokat befolyásol, de ezek látható szövegenkénti átlátszósági hatása nincs külön visszafejtve (§38.2.88).

**Fejlesztői átadás.** Még nem adható át: a 39%-os beúsztatás képlete megvan, de amíg nem tudjuk, melyik látható réteg a két kép, a PicasaPy-ban nem tudjuk, mire alkalmazzuk. A teljes programra futtatott `tagkereso.py 0x620 0x5f8` 95 találatot ad a qshow-tartományon kívül (a legtöbb a `0x00640670`-ban); az azonos eltolású mezőtalálatok közül csak a qshow-mutatóval bizonyított írók jöhetnek szóba. A következő hiányzó bizonyíték a két képmező tényleges tartalma/kitöltője és a `0x007fee70` felirat-paramétereinek látható hatása.

#### 38.2.88 A kiválasztott qshow-feliratok adatútja (#6532, 2026-11-05)

**Hatókör.** A helyi, SHA-256-tal azonosított `Picasa3.exe` qshow-feliratútját követtem a kiválasztott indextől a szövegrajzoló hívásig. A `idorend-job373.mp4` 6,000 és 10,000 másodperces képkockáin látható feliratokat ehhez a bináris úthoz hasonlítottam; ezek videómegfigyelések, nem futásidejű mezőkiolvasások.

**A kiválasztott indexű felirat és hónap/év.** A `0x007fee70` a qshow `[this+0x510]` mezőjéből veszi a kijelölt indexet (`0x007fee7f`-`0x007fee85`). A `[qshow+0x2f4]+0xc4` objektum a `CThumbDB`; a `CThumbDB+0x48` alobjektum virtuálistábla-címe `0x00c81fa4`. A programfájl virtuális táblájának tartalma és a közvetlen hívóutasítások alapján:

| qshow hely | hívás és kimenet | követhető cím |
|---|---|---|
| `0x007feebc`-`0x007feec1` | a `CThumbDB+0x48` virtuális tábla `+0x18` helyén át meghívja a `0x0044da40`-et; az indexhez egy szöveget ad vissza a `0x007fee70` helyi kimeneti objektumába. A `0x0044da40` a `this+0xb08` listából indexel, határon kívül a `this+0x5c` tartalék szöveget másolja. | virtuális tábla `0x00c81fa4`, `0x0044da40`, `0x005c2100` |
| `0x007feedf`-`0x007feee7` | a virtuális tábla `+0x20` helyén át meghívja a `0x0044f7c0`-at; az indexhez tartozó 64 bites dátumértéket írja a kimeneti címre, határon kívül a `this+0xc28` 64 bites értéket adja. | virtuális tábla `0x00c81fa4`, `0x0044f7c0` |
| `0x007feefb`-`0x007fef03` | a dátumértéket a `0x0098c780` `ytDateTime::Format2` függvénynek adja; a hozzá tartozó `%s %d` formátum a hónapnevet és az évet állítja elő. | `0x0098c780`, `0x00cd89c4`, `0x00c87dd0` |
| `0x007fef12`-`0x007fef43`, `0x007ff148`, `0x007ff1eb`, `0x007ff376` | a két visszaadott értékből szövegobjektumokat készít a `HelveticaNeue MediumCond` / `HelveticaNeue Condensed` betűkkel, majd a rajzoló virtuális hívásokhoz jut. | `0x00a48e10`, `0x009e6df0`, `0x00caf458`, `0x00caf474` |

A felvétel 6,000 és 10,000 másodperces képkockáin a jobb felső címkepár `2009_majus` és `May 2009`; a bináris út ugyanazon kiválasztott index szövegét és dátumát rajzolja. Ez a címkepár adatútját és a videón látható értékekkel való egyezést megerősíti. A `+0x510` szövegmező szemantikai oszlopneve és a mappanév forrása azonban a virtuális táblából önmagában nem olvasható ki; a „mappanév” megnevezés videóval korrelált címke, nem azonosított CThumbDB-oszlopnév.

**A teljes időbélyeg külön út.** A `0x007fee70` a `Format2` `%s %d` kimenetét rajzolja, tehát ez az út a hónap/év párt adja, nem a videón látható `2009-05-14 10:00` teljes dátum-időt. A `0x007fd180` képkártya-rutin a `0xf8` bájtos rekordok képadatát és geometriai mezőit dolgozza fel; a rekordonkénti `[record+0xa0] * p >> 8` értéket a `0x009e6df0` rajzolóhívásnak adja (`0x007fd300`-`0x007fd330`). A rutinban nincs dátumformázó hívás. A teljes dátum-idő mezőforrása, formázója és az azt kirajzoló hívás továbbra sincs összekötve.

**A nyitó képrétegek korlátja.** A `0x007fa7f0` konstruktor a `qshow+0x5f8` és `qshow+0x620` helyeken üres képtárolókat inicializál a `0x009a8a30` hívással (`0x007fab2c`-`0x007fab85`); a `0x007fb210` erőforrás-betöltő más qshow-mezőkbe tölti a felsorolt vezérlő- és `overlay` képeket. A `0x007ffc90` a két képtárolót ugyanazzal a legfeljebb `100/256` alfa-szorzóval keveri a képre. A videó 10,000 másodperces képkockáján a jobb felső címkepár fehér, a teljes időbélyeg halvány szürke; ez csak vizuális korreláció, és nem bizonyítja, hogy az időbélyeg vagy a halvány címke a `+0x5f8` / `+0x620` kép tartalma. A két képtároló tartalma és kitöltője nyitott.

**Állapot.** Lezárult: a `0x007fee70` kiválasztott-indexű szöveg- és hónap/év-adatútja, valamint az, hogy ez a `Format2` út nem adja a teljes `YYYY-MM-DD hh:mm` feliratot; a `0x007fd180` per-kártya alfaútja. Nyitott: a teljes időbélyeg mezője/formázója/rajzolója; a `+0x5f8` és `+0x620` tényleges tartalma és írója; a csíkozás eredete; a feliratút p-paraméterének pontos látható hatása; a felvétel pontos programfájl-hash-e. Ezek nélkül nem állítható össze a binárisan igazolt, teljes implementációs specifikáció, és nem adható át kész megvalósítási jegy.

#### 38.2.89 A Ghidra-dekompilálás a négy rétegfüggvényre (#6532, 2026-11-05)

**Forrás.** A Ghidra teljes dekompilálása a `0x007fee70` (feliratfestő), `0x007ffc90` (nyitó rétegkeverő), `0x007fd180` (kártya-animátor) és `0x00800a30` (időzítő) függvényre, hívottakkal: `referencia/ghidra/2026-11-05-idorend-6532-retegek.txt` (privát `picasapy-agent` repó, 976 sor). Mivel a dekompilálás a `0x007fee70` paramétereit hibásan vette fel (lásd lent), a kérdéses helyeket a helyi `Picasa3.exe` utasításain is ellenőriztem (capstone, `pe_dis.py`, csak a `0x007fee70`-`0x007ffc7f`, `0x007fe7c0`-`0x007fee6b` és `0x00801c80`-`0x00801f80` tartomány). A futó programfájl azonossága ugyanaz a korlát, mint a 38.2.86-ban: a bináris-állítások a helyi, hash-azonos programfájlra vonatkoznak.

**A dekompilálás egy hibája, amit tudni kell.** A Ghidra a `0x007fee70`-et egyparaméteresnek vette fel (`FUN_007fee70(int param_1)`), pedig az utasításai szerint három veremparamétere van (`ret 0xc` a `0x007fee9b` és `0x007ffc7f` címen): 1. a qshow (`this`, `[esp+0x174]`, `0x007fee78`), 2. a célkép (`[esp+0x180]`, `0x007ff05d`), 3. a `p` (`[esp+0x184]`, `0x007ff0c1`). A dekompilálásban az `iStack_1c`, `iStack_54`, `iStack_124`, `iStack_15c` nevű, sehol be nem állított változók valójában a `p` (és az `iStack_20`, `iStack_58`, `iStack_90`, `iStack_c8` a célkép). A hívó oldalán (`0x007ffc90`) a hívás helyesen háromargumentumos: `FUN_007fee70(in_EAX, unaff_EDI, param_1)`, ahol az `in_EAX` a qshow, az `unaff_EDI` a célkép, a `param_1` a `p`.

**Egyezés a korábbi szakaszokkal.** A dekompilálás megerősíti: a `0x00800a30` a `[this+0x430]` időből (`FUN_009a51b0(this+0x10c*4)`) `1.0` felső és `0.0` alsó korláttal számol, `256.0`-val szoroz, kerekít, és ezt adja a `0x007ffc90`-nek (`0x00800a30` két híváshelye; a `0x00c79c88` értéke `1.0`, a `0x00cf39d8` értéke `256.0`). A `0x007ffc90` a `p * 100 >> 8` értéket adja a `+0x620` és `+0x5f8` képnek a `0x009ab690`-nek (38.2.87). A `0x007fd180` rekordonként `(rekord[+0xa0] * p) >> 8` átlátszóságot ad a `0x009e6df0`-nek. A `0x007fee70` a `[this+0x510]` indexű szöveget és dátumot a `CThumbDB+0x48` virtuális tábla `+0x18` és `+0x20` helyén kéri (38.2.88).

**Két pontosítás a korábbi szövegekhez (nem a mért számokat érinti).**

1. A 38.2.86 és 38.2.88 azt írja, hogy a címkefestő út a `0x009e6df0`-hez jut. A `0x007fee70`-ben a `0x009e6df0` kizárólag a 10 pontot rajzoló ciklusban szerepel (`0x007ffc4d`, kép: `[this+0x6e8]`, a `timelinedot`); a szövegeket a betűobjektum virtuális tábla `+0x2c` hívása rajzolja (`0x007ff148`, `0x007ff1eb`, `0x007ff376`, `0x007ff3f5`, `0x007ff67f`, `0x007ff761`). Az `0x00a48e10` a betűobjektumot hozza létre, a `0x009e6df0` a szöveghez nincs kötve.
2. A 38.2.86 szerint a `0x007ffc90` "nem kap alfa-paramétert". A `p` neve haladás, de a `0x007ffc90`-ben és a hívottakban szinte minden elem átlátszósági szorzójaként működik (alább), tehát a nyitás első másodperce a felsorolt elemekre valóban beúsztatás. Az, hogy a *teljes panel* egyetlen átlátszósággal áll be, továbbra sem igazolt: a `0x007fe7c0` és az `overlay` (`+0x648`) nem kap `p`-t a `0x007ffc90`-ben.

**Címtáblázat.**

| Cím | Mit csinál | Forrás |
|---|---|---|
| `0x00800a30` | Zárral védett rajzoló. Ha a `[this+0x3b8]` bájt nem nulla, kiszámolja `p = kerekítés(min(max(t,0),1.0) * 256.0)`-t a `[this+0x430]`-ból, és hívja a `0x007ffc90`-et (két ág: `0x00800cc9`-`0x00800d46` és `0x00800f1d`-`0x00801003`). Ha a `[this+0x3b8]` nulla, csak a `0x008001c0` kártyarajzoló fut, `0x007ffc90` nem. A `+0x3c4`, `+0x444`, `+0x46c` képtárolókat a `0x009a9c90`/`0x009a8d80` méretezi és törli; a `+0x5f8`, `+0x620` tárolókhoz itt nem nyúl. | bináris (dekompilálás; `[this+0x3b8]`-ról nem tudjuk, mi) |
| `0x007ffc90` | Sorrend: `0x007fe7c0(this)`, `0x007fee70(this, cél, p)`, `+0x620` és `+0x5f8` kép `p*100>>8` szorzóval, `0x007fd180(this+0x2f8, cél, p)`, `+0x6c0` kép `p`-vel, a `+0x388` tömbből számolt pontok `+0x6e8` képpel `p`-vel, `+0x710` kép `p`-vel, végül a `0x007fe540` négy tesztje szerint a `+0x5a8` vagy a `+0x5d0` kép `p`-vel. | bináris (dekompilálás) |
| `0x007fee70` | Felirat- és vezetőpont-festő, részletek lent. Ha a `[this+0x510]` értéke `-1`, azonnal `4`-gyel visszatér. | bináris (utasítások `0x007fee85`-`0x007fee8c`) |
| `0x007fd180` | Az index-tömb (`obj[+0x80]`, darabszám `obj[+0x84] >> 1`) minden elemére a `0xf8` bájtos rekordot (`obj[+0xb0] + index * 0xf8`) rajzolja a `0x009e6df0`-nel, átlátszóság: `(rekord[+0xa0] * p) >> 8`. | bináris (dekompilálás) |

**a) A `p` látható hatása a `0x007fee70`-ben, szövegenként.** A `p` sehol nem mozgat pozíciót és nem szín-összetevőt választ: kizárólag a szövegszín bájtjait és a pontok átlátszóságát skálázza. A szövegrajzoló hívás (virtuális tábla `+0x2c`) színparamétere a `0x007ff0c1`-től:

| Szöveg | Betű (`0x00a48e10`) | Hely | Szín / átlátszóság `p`-ből | Cím |
|---|---|---|---|---|
| Gyűjtemény neve (a `CThumbDB+0x48` `+0x18` hívása a `[this+0x510]` indexre; a videón `2009_majus`) | `HelveticaNeue MediumCond` (`0x00caf458`), `0x190`, `0x1c`, méret `f32@0x00cf4144 = 0.7142857` | jobbra zárt: `x = [this+0x2d0] - 0x5a - szélesség`, `y = f32@0x00cf4e8c = 130.0` | árnyék: `(x+1, y+1)`-en, szín `((p * 0x7f0000) & 0xff00ff00)`, azaz fekete, alfa-bájt `floor(p*127/256)` (0-tól 127-ig). Utána a szöveg `(x, y)`-on, szín: mind a négy bájt `floor(p*255/256)` (`p=256`-nál `0xffffffff`). | `0x007ff0c1`-`0x007ff0cc`, `0x007ff148`; `0x007ff166`-`0x007ff180`, `0x007ff1eb` |
| Hónap és év (`ytDateTime::Format2`, `%s %d`, a `[this+0x510]` indexű dátumból; videón `May 2009`) | `HelveticaNeue Condensed` (`0x00caf474`), `0x190`, `0x14`, ugyanaz a `0x00cf4144` méret | jobbra zárt: `x = [this+0x2d0] - 0x5a - szélesség`, `y = f32@0x00cf4e88 = 158.0` | ugyanaz a két szín: előbb a fekete árnyék `(x+1, y+1)`-en, majd a világos szöveg `(x, y)`-on | `0x007ff376`, `0x007ff3f5` |
| A teljes qshow-lista első és utolsó rekordjának hónap/éve (videón `May 2009` és `November 2026` a dátumvonal két végén) | `HelveticaNeue MediumCond`, `0x190`, `0x0e`, méret `f32@0x00c7dbbc = 1.4` | a sáv (`[this+0x6d8]` bal x, `[this+0x6c8]` szélesség, `[this+0x6dc]+[this+0x6cc]` alsó y) két vége mellett: bal felirat jobbra zárva `[this+0x6d8] - 8`-nál, jobb felirat balra zárva `[this+0x6c8]+[this+0x6d8]+8`-nál, `y = alsó y - 3` | szín az árnyékszínből még egyszer skálázva: alfa-bájt `floor(floor(p*127/256) * p / 256)` (`p=256`-nál 127), fekete (rgb 0). Mindkét felirat ugyanazzal a színnel. | `0x007ff5da`-`0x007ff618`, `0x007ff67f`; `0x007ff6c1`-`0x007ff6f6`, `0x007ff761` |
| 10 vezetőpont (`[this+0x6e8]` kép) | nincs szöveg | lent | átlátszóság: `p` közvetlenül, a `0x009e6df0` utolsó argumentuma (`0x007ffc15`, `0x007ffc4d`) | `0x007ffc15`-`0x007ffc4d` |

A szín-bájtok jelentése ARGB-ként (az árnyék fekete és áttetsző, a szöveg fehér) olvasat: a szövegrajzoló belsejét nem vizsgáltam, tehát a bájtsorrendet nem igazoltam. A számítás maga (a színösszetevők kiválogatása és a szorzások) bináris. A `p` felső korlátja 256, ezért minden fenti érték 256-nál éri el a maximumát és utána nem változik.

**Vezetőpontok (10 db, a `0x007fee70` vége).** Feltétel: `[this+0x2f8] != -1` és a `[this+0x429]` bájt nulla (`0x007ff775`). Köbös Bézier-görbe mentén: `t = i / 9.0` (`f64@0x00cf3ef8 = 9.0`), `i = 0..9`. Pontok: `P0 = (A - 16, B)`, ahol `A`, `B` a két felirat helyi befoglaló téglalapjának jobb és alsó széle (`[esp+0xa0]`, `[esp+0xa4]`, `0x007ff268`-`0x007ff2c8`, `0x007ff7a9`); `P3 = ((r[+0xdc] + r[+0xe4]) * 0.5, r[+0xe0] - 20)`, ahol `r = [this+0x3a8] + [this+0x2f8] * 0xf8` a kijelölt rekord (`0x007ff7b4`-`0x007ff7f2`); `P1 = (P0.x, P0.y + 50)`, `P2 = (P3.x, P3.y - 50)` (`f64@0x00cf3bd8 = 50.0`). A pont `B(t) = (1-t)^3 P0 + 3(1-t)^2 t P1 + 3(1-t) t^2 P2 + t^3 P3` (`3.0` = `f64@0x00cf39f8`). Simítás: ha `[this+0x410]` nem nulla, a P0 és P3 mindkét koordinátáját `(előző + új) * 0.5`-re cseréli (`f64@0x00c72150 = 0.5`) és visszaírja a `[this+0x410..0x41c]` mezőkbe; ha nulla, a nyers értéket menti (`0x007ff810`-`0x007ff8e6`). Az átlátszóság `p`. A `P0` helyének pontos megnevezése (melyik felirat melyik széle) olvasat, a téglalap-egyesítés elágazásai nincsenek külön végigkövetve.

**b) A teljes `YYYY-MM-DD hh:mm` időbélyeg.** A négy függvény egyike sem rajzolja. A `0x007fee70` mindhárom dátumformázása (`0x007fef03`, `0x007ff4a9`, `0x007ff506`) a `0x0098c780` `ytDateTime::Format2`, amelynek egyetlen formátuma `%s %d` (`0x00c87dd0`), tehát csak hónapnevet és évet ad. A `0x007f0000`-`0x00808000` tartomány nyers hívásbájt-keresése (`e8` + eltolás a `0x0098c780`-ra) pontosan ezt a három helyet adja; a bináris index `string_xrefs.csv`-je szerint ebben a tartományban `%02d:%02d` jellegű formátum nincs. A `0x007fd180` és `0x00800a30` dekompilálásában nincs dátumformázó. A teljes dátum-idő forrása és formázója tehát ezen a négy függvényen belül nincs.

*Mellékes, kapcsolódó lelet (nem a négy függvény):* a `0x00801cf0` (`ret 4`, egy argumentum) a `[this+0x50c]` indexű gyűjtemény nevét (virtuális tábla `+0x18`) a `HelveticaNeue MediumCond`, `0x190`, `0x1c` betűvel egy gyorsítótár-képre (`[this+0x46c]`) rajzolja, színe `0xcfcfcfcf` (`0x00801f01`), és a QPC-t a `[this+0x520]`-ba menti (`0x00801f1b`-`0x00801f30`). Ebben a függvényben egyetlen szövegrajzoló hívás van (`0x00801f14`) és nincs dátumformázó. Ez a "halvány szürke" nagy bal oldali felirat névrésze lehet; a dátum-idő rész nem itt van.

**c) A `+0x5f8` és `+0x620` kép.** A négy függvényben ezekre kizárólag a `0x007ffc90` hivatkozik (`this+0x620`, `this+0x5f8`, mindkettő `p*100>>8` szorzóval, `0x009ab690`), a `0x00800a30` nem nyúl hozzájuk. A tartalmukra vagy a kitöltőjükre semmi nem utal ezen a négy függvényen belül. A `0x007fee70` kimenete (szöveg, pont) célképre megy, nem ezekbe. A kitöltő a kódból nem olvasható ki, így jelöltet sem nevezek meg; a 38.2.87 már kizárta a `0x007fb210` betöltőt és a `0x007f0000`-`0x00808000` tartomány többi függvényét (csak konstruktor `0x007fa7f0` és felszabadító `0x007fb5a0` nyúl hozzájuk). A következő vizsgálat nem egyetlen címhez köthető jelölt, hanem módszer: a 38.2.87 95 tagkereső-találata közül azokat kell végigvenni, amelyek qshow-mutatóval érik el a `+0x5f8`/`+0x620` mezőt, és a konstruktor `0x009a8a30`-cal létrehozott üres tárolóit kitöltő hívásokat kell keresni (`0x009a9c90` méretezés, majd rajzolás a tárolóba).

**d) A `0x007fd180` kártya-pálya.** A `p` itt *csak* átlátszóságot skáláz. Pozíciót és méretet nem számol belőle. Rekordonként (`r = obj[+0xb0] + obj[+0x80][i] * 0xf8`):

- bemásolja az `r[+0xdc..+0xe8]` négy szót (`local_60..local_54`) és az `r[+0xa4..+0xcc]` tíz szót (`local_50`);
- ha az `r[+0xc8]` bájt nulla, az átalakítás a `0x00a4a140` alapértéke (9 lebegőpontos szám, `local_8c = 0`); ha nem nulla, a mátrix `[1, 0, -r[+0xac]; 0, 1, -r[+0xb8]]` és `local_8c = 1` (az `r[+0xac]` és az `r[+0xb8]` az `r[+0xa4]` másolat 3. és 6. szava);
- ha az `r[+0x30]` nem nulla: `0x00a6ac90(r+4, mátrix, f32@0x00c7dd44 = 1.2)`, majd `0x009a8ca0`, `0x009a8bc0`;
- rajzolás: `0x009e6df0(cél, &local_88, mátrix, 1, 1, (r[+0xa0] * p) >> 8)`.

Vagyis a kártya képernyőhelyét és méretét az `r` rekord `+0xa4..+0xcc` mezői és a `0x00a6ac90` adja, amelyet a rekordokat író `0x007fff30` és `0x00802230` tölt (38.2.61-62). A `p`-től független képlet ebből a függvényből nem olvasható ki. A `0x00a6ac90` belsejét és a `0x00cf3a48` (`2.0f`) rekordokhoz kötését nem vizsgáltam.

**Ellentmondás.** A fenti 1. pontosítás (a szöveg nem a `0x009e6df0`-n át megy) a 38.2.86 és a 38.2.88 egy-egy mondatával ellenkezik; a mért értékeket, a `p` képletét, a `100/256` szorzót és a `[record+0xa0] * p >> 8` alakot nem érinti.

**Következtetés.** (1) Bináris: a `p` a nyitás első másodpercében 0-tól 256-ig lineárisan nő, és a `0x007ffc90` szinte minden elemén átlátszósági szorzó (a két képen `100/256`-ra korlátozva, a szövegszíneken és a vezetőpontokon a fent megadott módon). (2) Bináris: a `0x007fee70` a jobb felső feliratpárt (név és hónap-év), a dátumvonal két végének hónap-év feliratát és a 10 vezetőpontot rajzolja. (3) Bináris: a teljes `YYYY-MM-DD hh:mm` felirat és a `+0x5f8`/`+0x620` tartalma ezen a négy függvényen kívül van.

**Nyitott.**

- A teljes dátum-idő felirat mezője, formázója és rajzolója. Kiindulás: a `0x00801cf0` testvérfüggvényei a `0x00801cc1`-`0x00801ce5` körüli hívásláncban (`0x007fc010`, `0x007fd8c0`, `0x008018a0`) és a `[this+0x46c]`/`[this+0x470]` kép használói; ezeket ebben a körben nem olvastam végig.
- A `+0x5f8` és `+0x620` kitöltője (lásd c).
- Mi a `[this+0x3b8]` bájt (a `0x007ffc90` hívásának feltétele a `0x00800a30`-ban), és mit rajzol a `0x007fe7c0` (a `[this+0x3c4]` kép a `0x007fee06`-nál, a `[this+0x3bc]`/`[this+0x3bd]` bájtoktól függően, `p` nélkül).
- A `0x00a6ac90` (f32 `1.2` paraméterrel) és a rekordmezők `+0xa4..+0xcc` pontos jelentése; az `overlays/overlay` (`+0x648`) rajzolója továbbra sem a négy függvény egyike.
- A ferde csíkozás eredete.

**Fejlesztői átadás (csak binárisból igazolt elemek).**

| Eredeti | Teendő |
|---|---|
| `p = kerekítés(min(max(t, 0), 1.0) * 256.0)`, `t` = QPC-másodperc a nyitás óta (`0x00800a30`, `0x00c79c88`, `0x00cf39d8`) | A nyitó beúsztatás időalapja 1 s. A 1.000 s a videón is látszik (**csak mérés**: 38.2.85). |
| Jobb felső név: fekete árnyék `(x+1, y+1)`, alfa `floor(p*127/256)`; szöveg `(x, y)`, alfa és szín `floor(p*255/256)`; `x = szélesség_qshow - 0x5a - szövegszélesség`, `y = 130` (`0x007ff0c1`-`0x007ff1eb`, `0x00cf4e8c`) | Nálunk a felirat átlátszóságát a nyitás első másodpercében 0-ról lineárisan növelni. Betű: `HelveticaNeue MediumCond`, méretadat `0x00cf4144 = 0.7142857` (a mértékegységet a betűobjektum adja, nem igazoltam). |
| Jobb felső hónap-év: ugyanaz a két szín, `HelveticaNeue Condensed`, `y = 158` (`0x007ff376`, `0x007ff3f5`, `0x00cf4e88`) | Ugyanaz. A szöveg `ytDateTime::Format2` `%s %d` (hónapnév + év). |
| Dátumvonal két vége: első és utolsó rekord hónap-éve, fekete, alfa `floor(floor(p*127/256)*p/256)`, `HelveticaNeue MediumCond`, `0x0e`, méret `1.4`; bal felirat jobbra zárva a sáv bal széle mínusz 8-nál, jobb felirat balra zárva a sáv jobb széle plusz 8-nál, `y = sáv alja - 3` (`0x007ff5da`-`0x007ff761`) | Ezek a `May 2009` és `November 2026` feliratok. A szín (fekete) az utasításokból olvasat; a vizuális egyezés a videóval nincs mérve. |
| 10 vezetőpont a kijelölt kártya felé: köbös Bézier, `t = i/9`, `P1 = P0 + (0, 50)`, `P2 = P3 - (0, 50)`, `P3 = ((r[+0xdc]+r[+0xe4])/2, r[+0xe0]-20)`, simítás `(előző+új)*0.5`, átlátszóság `p` (`0x007ff775`-`0x007ffc4d`, `0x00cf3ef8`, `0x00cf3bd8`, `0x00c72150`) | A PicasaPy ívét (`TimelinePanel.qml:60-138`) ehhez képest ellenőrizni; a P0 helye (a két felirat befoglalójának jobb alsó sarka mínusz 16) olvasat. A pontok mérete és közepe nem igazolt. |
| Kártyák átlátszósága: `(r[+0xa0] * p) >> 8` (`0x007fd180`) | Ez csak a nyitó beúsztatás szorzója; a kártya saját `r[+0xa0]` alfáját a `0x007fff30` adja (38.2.62). |
| `+0x6c0`, `+0x6e8` (sáv pontjai), `+0x710`, és a `+0x5a8`/`+0x5d0` vezérlőképek `p` átlátszósággal; a `+0x5f8`/`+0x620` kép `p*100>>8`-cal (`0x007ffc90`) | A vezérlősáv is beúszik az első másodpercben. A `+0x5f8`/`+0x620` tartalma nincs meg, ezért átvehető teendő nincs. |

**Új kutatási jegyjavaslat.** Nincs. A nyitott pontok a #6532 hatókörében maradnak.

#### 38.2.90 A gyűjteménynév-rajzoló hívásláncának két függvénye (#6532, 2026-11-05)

**Forrás.** A Ghidra-dekompilálás a `0x008018a0` és a `0x007fd8c0` függvényre, hívottakkal: `referencia/ghidra/2026-11-05-idorend-6532-datumfelirat.txt` (privát `picasapy-agent` repó, 307 sor). A Ghidra paraméterszáma itt is megbízhatatlan, ezért mindkét függvényt, a hívó `0x00801cb0`-t és a hívottakat a helyi `Picasa3.exe` utasításain is végigolvastam (capstone, `pe_dis.py`). A `_DAT_` konstansokat a programfájlból olvastam ki (`pe_dis.py` `f32`/`f64`). A bináris-állítások a helyi, hash-azonos programfájlra vonatkoznak (ugyanaz a korlát, mint a 38.2.86-ban).

**A hívólánc.** A `0x00801cb0` (nincs veremparamétere, a qshow a `esi`-ben) a `0x00801cc1`-nél hívja a `0x007fc010`-et (`this+0x2f8`, `this+0x2c8`), majd, ha a `[this+0x429]` bájt nulla, a `0x00801cd8`-nál a `0x007fd8c0`-at (`eax = this+0x2f8`, a veremparaméter `this+0x510` címe). Ha az igazat ad, a `0x00801ce1`-nél a `[this+0x510]` értékét az `eax`-be tölti, és hívja a `0x008018a0`-at (`ecx = this`). A `0x007fd8c0` paramétere tehát egy *kimenet*: ide írja a kiválasztott gyűjtemény sorszámát.

**Címtáblázat.**

| Cím | Mit csinál | Forrás |
|---|---|---|
| `0x00801cb0` | Egy lépés: `0x007fc010` (görgetés léptetése), majd `0x007fd8c0` (fókuszkártya kiválasztása), majd, ha az igazat ad, `0x008018a0` (gyűjteményváltás). | bináris (utasítások `0x00801cb0`-`0x00801cef`) |
| `0x007fd8c0` | A kártyasáv (`obj = this+0x2f8`) minden rekordjára `t = i * [obj+0x30] + [obj+0x20]` (f64 mezők), meghívja a `0x007fbab0` görbét, és a görbe pontjának első összetevőjét az `0.666` (f64 `0x00cf4860`) értékhez méri. A legkisebb eltérésű rekord sorszáma a `[obj+0]`-ba (`this+0x2f8`) kerül, a rekord (`obj[+0xb0] + sorszám * 0xf8`) első szava pedig a kimenetre (`[this+0x510]`). Visszatérési érték: igaz, ha a sáv megállt (lent). | bináris (`0x007fd8c0`-`0x007fd9f0`) |
| `0x007fbab0` | Háromdimenziós köbös Bézier-görbe: a `ecx` objektum `+0x50..+0x7c` mezőiben négy, három lebegőpontos számból álló ellenőrzőpont, a bemenet az `t` (f32 a veremben), a kimenet három f32 (a `eax`-ben megadott helyre, `eax` vissza). A `0x007fc010` a harmadik összetevőt a `0.1`-hez (f64 `0x00c7dd30`) hasonlítja: a sáv láthatósági szűrője. | bináris (`0x007fbab0`-`0x007fbbe5`, a `0x007fc010` `0x007fc100`-`0x007fc128`) |
| `0x008018a0` | Gyűjteményváltás. Ha a `[this+0x50c]` már egyezik az `eax`-szel, azonnal kilép. Különben beírja az új sorszámot a `[this+0x50c]`-be, a `[this+0x2f4]` objektumból kéri a gyűjtemény elemlistáját (`0x004b0190`, zár alatt), a `[this+0x3ec]` listát (darabszám `[this+0x3f0] >> 1`) újraépíti a nem kizárt elemek azonosítóival, nullázza a `[this+0x3f4]`-et, a `[this+0x51a]` bájtot 1-re állítja, majd hívja a `0x008014d0`-et. | bináris (`0x008018ac`-`0x00801c19`; a ciklus tartalma dekompilálásból) |
| `0x008014d0` | A gyűjtemény elemeihez kártyakészletet épít: a régi `[this+0x2ec]` objektumot felszabadítja (`0x00803c10`), az új elemeket a `[this+0x2e4]` objektum virtuális hívásával kéri, a hely véletlen eltolását `rand`-szerű hívásokból (`0x00c08221`) számolja. Szöveget nem rajzol. | bináris (hívások `0x008014e5`-`0x00801862`; a szerep olvasat) |

**1. A nagy bal oldali teljes dátum-idő felirat. Nem ez a két függvény.** Egyik sem hív szövegrajzolót vagy betűobjektumot (`0x00a48e10`), egyik sem hív dátumformázót (`0x0098c780` és társai), és a közvetlen hívási listájukban sincs ilyen (Ghidra hívottak: `0x008018a0` kilenc, `0x007fd8c0` három hívott, köztük nincs formázó vagy rajzoló). A `0x008018a0` a *gyűjtemény váltását* végzi: elemlista és kártyakészlet cseréje. A `0x007fd8c0` a *fókusz* kiválasztását végzi. Mezőt, formázót és képet a dátum-idő feliratra tehát nem lehet belőlük megnevezni.

**Mit számol a `0x007fd8c0` pontosan.**

- Fókusz: a `t = i * [obj+0x30] + [obj+0x20]` helyen a görbe pontjának első összetevője (f32) és az `0.666` különbségének abszolút értéke (`0x0049f5c0` = `fabs`) a legkisebb. A kezdő minimum f32 `1000000.0` (`0x00cf4900`). Döntetlennél az előbbi (kisebb sorszámú) marad (`fcomp`, `0x41` maszk).
- Megállt-e: igaz, ha `|[obj+0x18]| <= [obj+0x30] * 0.01` (f64 `0x00cf40b8`) *és* a `[obj+0x4c] >> 1` darabszámú szakaszlistán (`[obj+0x48]`) nincs befejezetlen szakasz: nulla szakasznál igaz, két vagy több szakasznál hamis, egynél igaz, ha a kezdő és záró idő (`+0x18`, `+0x20`) egyenlő, vagy `(most - kezdő) / (záró - kezdő) > 1.0` (f64 `0x00c7e328`). A `most` a `0x009a5210` értéke: másodpercben a QueryPerformanceCounter-idő az első híváshoz képest (`0x009a5210`, a frekvencia-gyorsítótár `0x00d678e8`).

**2. A `+0x5f8` és `+0x620` képtároló. Nem írnak bele.** A `0x007fd8c0` teljes utasítássorában (`0x007fd8c0`-`0x007fd9f0`) és a `0x008018a0` utasításaiban (`0x008018a0`-`0x00801caf`) nincs `+0x5f8` vagy `+0x620` hivatkozás (a `0x008018a0` csak a `+0x20`, `+0x24`, `+0x28`, `+0x2f4`, `+0x3ec`, `+0x3f0`, `+0x3f4`, `+0x50c`, `+0x51a` és `+0xc` eltolásokat használja); a `0x008014d0` első `0x3d0` bájtjában sincs. A `0x008014d0` hátralévő része és a `0x00803c10`, `0x00803b50` nincs végigolvasva.

**3. A `0x007fd8c0` és a görbe. Képlet és kapcsolat az 1,4 mp-hez.**

- A görbe *térbeli pálya*, nem időgörbe: a `t` paraméter a kártya sorszámából és a sáv görgetési eltolásából jön (`t = i * lépés + eltolás`), nem az órából. A kimenete (x, y, z) a kártya helye és mélysége a sávban. Az ellenőrzőpontok futásidejű mezők (`this+0x348..0x374`), a konstruktor (`0x007fa7f0`) vagy egy beállító tölti őket; az értékeiket nem olvastam ki.
- A `0x007fbab0` egyetlen kiolvasható konstansa a `3.0` (f64 `0x00cf39f8`, a Bézier-súly). A teljes Bernstein-szorzat az utasításokból olvasat (`(1-t)^3`, `3(1-t)^2 t`, `3(1-t) t^2`, `t^3`).
- Időt a `0x007fd8c0` csak a *megállt-e* ágban használ (`0x009a5210`, másodperc), és ott is szakaszarányt (`> 1.0`), nem 1,4 másodpercet. Nincs `1.4` vagy hozzá közeli időállandó a két függvényben vagy a `0x007fbab0`-ban. A `0x007fc010` a sebességet hívásonként `0.95`-tel szorozza (f64 `0x00cf40b0`), ami képkockaszámhoz kötött lassulás; ebből az 1,4 mp nem vezethető le a hívási gyakoriság ismerete nélkül. **A lapváltás mért kb. 1,4 mp-éhez (38.2.85, csak mérés) kapcsolat nem igazolt.**

**Ellentmondás a korábbiakkal.** Nincs. A 38.2.89 sejtése, hogy a `0x00801cf0` testvérfüggvényei a dátum-idő feliratot adhatják, ezzel megdőlt erre a két függvényre.

**Mellékes lelet a gyűjteménynév-gyorsítótárról (nem a kérdés, de a keresést szűkíti).** A `0x00801cf0` a nevet a `[this+0x46c]` képre rajzolja; a `0x00802130` ezt a képet szürkeárnyalatúvá teszi (minden képpont a zöld bájt háromszorosa `0x10101`-gyel szorozva). A `[this+0x470]` nem külön kép, hanem a `+0x46c` kép sorhossza (a `0x008001c0` `0x008004af`-nál `[ebp+0x470] * sor` indexel a `[ebp+0x47c]` képpontterületen). A `0x008001c0` a `+0x444` és `+0x46c` képet képpontonként keveri (`0x009dc040`), a `0x00802230` a `0x009ad280` hívással a `+0x46c`-t a `+0x444` helyére másolja (`0x00802516`-`0x00802525`); ez átúsztatásra (a régi és az új név) utal, de a keverés mértékét nem olvastam ki. A `[this+0x3b8]` bájt szerepe nyitott marad.

**Következtetés.** (1) Bináris: a `0x008018a0` gyűjteményváltás (elemlista és kártyakészlet cseréje), a `0x007fd8c0` fókuszválasztás a görbe első összetevője és `0.666` különbsége szerint, plusz megállt-teszt. (2) Bináris: egyik sem formáz vagy rajzol szöveget, egyik sem nyúl a `+0x5f8`/`+0x620` tárolóhoz. (3) Kizárt: a két függvény mint a nagy bal oldali `YYYY-MM-DD hh:mm` felirat forrása. (4) Nem igazolt: kapcsolat a mért 1,4 mp-hez.

**Nyitott.**

- A teljes dátum-idő felirat mezője, formázója és rajzolója. Kizárt helyek: a `0x007fee70` (csak `%s %d`), a `0x00801cf0` (csak név), a `0x008018a0`, a `0x007fd8c0`. A `ytDateTime` formázók hívói a programban: `0x0098c780` (`%s %d`) hívói `0x0043c410`, `0x004b0390`, `0x004b3770`, `0x007376a0` (filmkészítő, `CMovieExport::renderprog`, nem qshow), `0x007fee70`, `0x0086bce0`, `0x0087db30`; a `0x0098c670` (`MMM d, yyyy`) hívói között a `0x007f9880` (a qshow konstruktor `0x007fa7f0` közvetlen szomszédja, 231 bájt) áll, amelyet nem olvastam végig; a `0x0098c9a0` (`%.2d:%.2d:%.2d`) hívói videó- és filmkezelők (`video_control_bar`, `makemoviepanel`), nem qshow.
- Az időpont forrása: a `CThumbDB+0x48` virtuális tábla `+0x20` helyén a `0x0044f7c0` a gyűjteményhez tartozó időt *f64 számként* adja (a tömb `[objektum+0x58]` mutatóján át, `[+0x48][sorszám]`, 8 bájtos elemek); a tábla címe `0x00c81fa4` (a konstruktorok `0x00415804` és `0x0041777f` a `[this+0x48]`-ba írják). Ez az idő tehát időbélyeg, nem szöveg: a formázás a hívónál történik.
- A `0x008014d0` hátralévő része, a `[this+0x3b8]` bájt szerepe, a `0x007fbab0` ellenőrzőpontjainak értékei.

**Következő két cím (kódból kiolvasható indokkal).**

1. **`0x007f9880`** (231 bájt). Indok: a `0x007f98ab`-nál a `0x0098c670` (`MMM d, yyyy`) dátumformázót hívja, a végén `ret 8`, a qshow konstruktor `0x007fa7f0` közvetlen szomszédja a programszövegben. Ez az egyetlen dátumformázó-hívó a `0x007f0000`-`0x00808000` tartományban, amelyet a 38.2.88 és 38.2.89 nem vizsgált (a `0x0098c780`-ra és a `%02d:%02d` jellegű sztringekre szűkített). Ha a hívója qshow-mutatót kap, vagy a `[this+0x510]`/`[this+0x50c]` sorszámot használja, ez a dátumfelirat forrása; ha nem, a qshow-tartomány dátumfeliratok szempontjából lezárható.
2. **`0x0044f7c0`** (a `CThumbDB+0x48` tábla `+0x20` helye, a gyűjtemény ideje f64-ként). Indok: ez a `0x007fee70` dátumának és minden más qshow-dátumnak az egyetlen forrása a kódban; a hívóinak keresése (a `[reg+0x20]` hívás `ecx = objektum+0x48` mellett) megmutatja, melyik másik függvény kéri el a gyűjtemény idejét, és mit kezd vele (formázó, szövegrajzoló).

**Fejlesztői átadás (csak binárisból igazolt elemek).**

| Eredeti | Teendő |
|---|---|
| A fókuszkártya a sáv azon rekordja, amelynek görbepontja első összetevője legközelebb esik `0.666`-hoz (`0x007fd8c0`, `0x00cf4860`) | A PicasaPy fókuszválasztását ehhez a szabályhoz hasonlítani; a görbe ellenőrzőpontjait nem ismerjük, ezért átvehető képlet még nincs. |
| A sáv megállt, ha a sebesség abszolút értéke legfeljebb a rekordlépés századrésze (`0.01`), és nincs futó szakasz (`0x007fd8c0`) | Csak megerősíti, hogy a gyűjteményváltás a görgetés megállása után történik, nem közben. |
| A gyűjteményváltás (`0x008018a0`) csak akkor fut, ha a `[this+0x429]` bájt nulla, és a kiválasztott gyűjtemény sorszáma eltér a korábbitól (`0x00801cc6`, `0x008018ac`) | A kiválasztott gyűjtemény elemlistáját és kártyakészletét a görgetés megállása után cserélni. |
| A teljes `YYYY-MM-DD hh:mm` felirat forrása | Nincs; nem igazolt, ezért nincs átvehető teendő. |

**Új kutatási jegyjavaslat.** Nincs; a nyitott pontok a #6532 hatókörében maradnak.

#### 38.2.91 A két utolsó dátumjelölt kizárása (#6532, 2026-11-05)

**Forrás.** Ghidra-dekompilálás, hívókkal és hívottakkal: `referencia/ghidra/2026-11-05-idorend-6532-datumformazo.txt` (privát repó), valamint a bináris index `xrefs.csv` és `string_xrefs.csv` táblája.

| cím | mit csinál |
|---|---|
| `0x007f9880` | Egyetlen hívója a `0x007f9130` (`0x007f9252`). A rekordokon `0xe0` bájtos lépéssel megy végig; rekordonként meghívja a `0x0098c670` dátumformázót (`0x007f98ab`), a rekord `+0x3c` helyéről vett nevet és a kapott dátumszöveget a `0x008e3730`-nak adja (`sorszám, név, dátumszöveg, 0`), majd a második paraméter `+0x48` objektumán a virtuális tábla `+0x100` helyét hívja `(sorszám, 1)` értékkel. Rajzoló- vagy betűobjektum-hívás nincs benne, qshow-mezőt (`+0x510`, `+0x46c`, `+0x5f8`, `+0x620`) nem olvas. |
| `0x0044f7c0` | A `CThumbDB+0x48` virtuális tábla `+0x20` helye. Két zárolás között a `[this+0xc20]+0x48` tömbből a kért sorszámú 64 bites értéket adja vissza, határon kívül a `[this+0xc28]` tartalékot. Formázást nem végez. Hívói: a `0x0049f270` és a virtuális tábla (`0x00c81fc4`). |

**Kereszthivatkozás-leltár a `0x007f0000`-`0x00808000` tartományra** (`xrefs.csv`, közvetlen hívások): a dátumformázók közül csak a `0x0098c780` (`Format2`, a `0x007fee70`-ből háromszor) és a `0x0098c670` (a `0x007f9880`-ból) kap hívást. A `%Y-%m-%d` formázó (`0x0098cba0`), a `HH:mm:ss` formázó (`0x0098bf10`) és a `%.2d:%.2d:%.2d` formázó (`0x0098c9a0`) innen nem kap közvetlen hívást. Ez index-alapú leltár: a virtuális táblán át futó hívásokat nem látja, ezért önmagában nem kizárás.

**Következtetés.** A `0x007f9880` nem a nagy kártya dátum-idő felirata: soronként egy nevet és egy dátumszöveget ad tovább egy listaszerű objektumnak, és nem rajzol. A `0x0044f7c0` puszta adatkiolvasó. A 38.2.88-38.2.91 négy körében vizsgált qshow-függvények egyike sem állítja elő a `2009-05-14 10:00` alakot. A felvétel szerint ez a felirat a nagy kártyán, a mappanév mellett látszik (38.2.81), ezért a kártyakép összeállítása a következő hely: a `0x008014d0` kártyakészlet-építő két, eddig végig nem olvasott hívottja, a `0x00803c10` és a `0x00803b50` (közös hívójuk a `0x007fc7c0` is).

**Nyitott.** A `0x00803c10` és a `0x00803b50` tartalma (azóta lezárva, `referencia/ghidra/2026-11-05-idorend-6532-kartyaepito.txt`: a `0x00803c10` a `0xf8` bájtos kártyarekord-tömb felszabadítója, elemenként a `0x007fd090` bontót hívja; a `0x00803b50` a kártyarekord másolója, a `+4` képet a `0x00a6a7d0`-val, a `+0xf0` 64 bites mezőt közvetlenül veszi át; egyikben sincs dátumformázás vagy szövegrajzolás); ha ezek sem formáznak dátumot, a következő lépés a virtuális táblán át hívott formázók mintára pásztázása a kártyaépítő láncban.

**Fejlesztői átadás.** Nincs új, binárisból igazolt megvalósítási elem.

#### 38.2.92 A qshow szövegrajzoló helyeinek teljes leltára (#6532, 2026-11-05)

**Forrás.** Ghidra-dekompilálás a `0x008014d0` teljes hosszára és a `0x007fc7c0`-ra, hívottakkal: `referencia/ghidra/2026-11-05-idorend-6532-kartyakeszlet.txt` (privát `picasapy-agent` repó, 620 sor). A leltár a helyi `Picasa3.exe` bájtjain készült (ugyanaz a programfájl, mint a 38.2.86-ban: PE-verzió `3.9.141.259`, SHA-256 `644b7bec...ddc96`, egyezik a bináris indexével; a videóban futó példány azonossága továbbra sem igazolt, a bináris-állítások a helyi fájlra szólnak). Eszköz: `pe_dis.py` és kis capstone-szkriptek, a PE import-táblájából saját kiolvasással az IAT-nevek (a bináris index `imports.csv` a névtábla címét adja, nem a hívott IAT-rést).

**Módszer és hatókör.** A pásztázás a `0x007f0000`-`0x00808000` tartomány egészére szól, nem jelöltenként. Négy független út:

1. *Nyers hívóutasítások* (`e8` + relatív eltolás) a tartomány minden bájtján, nem csak a bináris index xrefs-én: a betűobjektum-készítőre (`0x00a48e10`), a képrajzolóra (`0x009e6df0`) és a két dátumformázóra (`0x0098c780`, `0x0098c670`).
2. *Nyers címhivatkozások* (32 bites érték) a két betűnév-szövegre, és a programfájl **összes** betűnév-szövegére (`Helvetica...`, `Arial`, `Arial Unicode MS`, `Lucida Console`, `Georgia`, `Times`, `Tahoma`, `Impact`), valamint a szövegosztályok virtuálistábla-címeire (`ytSkiaTextRender`, `ytVectorTextNode`, `ytMultiTextNode`, `ytTextSettings`, `CTextCaptionCreator`, `ytFontCache`).
3. *Utasítás-pásztázás* a bináris index mind a 247 függvényén (`functions.csv`, `.text`, ebben a tartományban): minden közvetett hívás (`call reg`, `call [reg+...]`), amely előtt két darab `sub esp, 0x10` blokk áll. Ez a szövegrajzoló hívás alakja: két 16 bájtos szerkezet a veremben, négy érték, két nulla; a hívott függvény `ret 0x38`-cal tér vissza. A virtuális hívásokat az xrefs nem látja, ez igen.
4. *Az összes Win32 szöveg-hívás* (`TextOut*`, `ExtTextOut*`, `DrawText*`, `CreateFont*`, `SetWindowText*`, `SendMessage*`) a PE import-táblája szerint feloldva.

A betűobjektum osztálya: a `0x00a48e10` visszatérési értékének virtuális táblája `+0x2c` helyén `0x007ff141`-nél a hívott függvény a `ytFontCache::vftable` (`0x00ce400c`) 12. bejegyzése, a `0x00a46bb0` (`ret 0x38`, azaz 14 szó argumentum). Az, hogy a `0x00a48e10` által adott objektum ennek az osztálynak a példánya, olvasat: az argumentumszám egyezik, és az osztály neve (`ytFontCache`) az RTTI-táblából jön; az objektum létrehozását és azt, hogy a `0x00a48e10` valóban ilyen példányt ad, nem követtem végig.

**Hatókörön kívül maradt:** a függvényhatárokon kívüli bájtok (a `functions.csv` nem sorol fel mindent), a tartományon kívüli hívók, és az olyan szövegrajzolás, amely nem a `0x00a46bb0`-n, hanem függvénymutatón vagy a `ytSkia` / `ytVectorTextNode` úton megy (a tartomány nem hivatkozik ezek táblájára: a 2. pontban a vtábla-címekre nulla találat).

**Eredmény: a betűobjektum-készítő összes hívása és a szövegrajzoló összes hívása.**

| Cím | Függvény | Mit csinál | Melyik képre | Forrás |
|---|---|---|---|---|
| `0x007fef21`, `0x007fef43`, `0x007fef69` | `0x007fee70` | Három betű: `HelveticaNeue MediumCond` (0x190, 0x1c, méret `0.7142857`), `HelveticaNeue Condensed` (0x190, 0x14), `HelveticaNeue MediumCond` (0x190, 0x0e, méret `1.4`). | nincs (betűkészítés) | bináris (nyers hívóutasítás) |
| `0x007ff148`, `0x007ff1eb` | `0x007fee70` | Gyűjtemény neve (a `[this+0x510]` indexű gyűjtemény, `CThumbDB+0x48` virtuális tábla `+0x18`): fekete árnyék `(x+1, y+1)`, majd szöveg `(x, y)`, `y = 130`. | célkép (a `0x007ffc90` adja) | bináris (38.2.89, itt újra megtalálva) |
| `0x007ff376`, `0x007ff3f5` | `0x007fee70` | Hónap és év (`ytDateTime::Format2`, `%s %d`): árnyék, majd szöveg, `y = 158`. | célkép | bináris |
| `0x007ff67f` | `0x007fee70` | A dátumvonal bal vége: az első rekord hónapja és éve. | célkép | bináris |
| `0x007ff761` | `0x007fee70` | A dátumvonal jobb vége: az utolsó rekord hónapja és éve. | célkép | bináris |
| `0x00801dc6`, `0x00801f14` | `0x00801cf0` | Egy betű (`HelveticaNeue MediumCond`, 0x190, 0x1c) és egyetlen szövegrajzolás: a `[this+0x50c]` indexű gyűjtemény neve, szín `0xcfcfcfcf`. Más szöveg és dátumformázó nincs benne. | a `[this+0x46c]` gyorsítótár-kép | bináris |
| `0x007f0ec7` | `0x007f0d90` | Egy `Arial` betű (0x190, 0x24, méret `1.4`), az objektum `+0x250` mezője `-4`. A függvényben szövegrajzoló hívás **nincs**; a névjegy-ablak szövegeit (`IDS_ABOUT1`, `IDS_ABOUT_LINUX`) Win32-vezérlők kapják (`GetDlgItem`, `SendMessageA`). Nem qshow. | nincs | bináris |

A tartományban tehát **7 szövegrajzoló hívás van, két függvényben** (`0x007fee70`: 6, `0x00801cf0`: 1), és **5 betűobjektum-készítő hívás** (ebből 1 a névjegy-ablaké). Más hely nem hívja a `0x00a48e10`-et, nem hivatkozik a `HelveticaNeue` szövegekre, és nem hívja a `0x00a46bb0`-t (sem közvetlenül, sem a fenti hívásalakkal). A nyers `e8`-keresés és az utasítás-pásztázás ugyanezt a halmazt adta.

**Ami szöveggel foglalkozik, de nem ezzel a rajzolóval:**

| Cím | Mit csinál | Miért nem a kérdés |
|---|---|---|
| `0x007f9880` | `0x0098c670` (`MMM d, yyyy`) dátumszöveg soronként, továbbadva egy listának. | Nem rajzol (38.2.91). |
| `0x00802ff0` | `OneUpUI::Format` (`%d %s`, "second"/"seconds"): a másodperc-felirat az egyképes diavetítés UI `oneup/tps` elemére. | Más osztály (OneUp UI), a szöveget a UI-elem kapja, nem a betűobjektum. |
| `0x00802c60`, `0x00802ec0` | A OneUp UI konstruktora (`i18n\oneuptext.xml`, `oneup/caption`, `oneup/stripback`) és a képaláírás-frissítő: a `[this+0x260]` szolgáltatótól kér szöveget (virtuális tábla `+0x14`), és a `oneup/caption` elemnek adja. | A szöveg forrását (a szolgáltató) nem olvastam. Nyitott. |
| `0x007f1270` | `CreateFontIndirectA`, `GetTextFaceA`, `SetTextColor`: Win32-betűsegéd. | Ablakos vezérlő, nem qshow. A tartalmát nem olvastam végig. |
| `0x007f0000`-`0x007f9700` többi függvénye | Névjegy-ablak, webes exportálás, RSS-letöltő, Google Fotók import: szövegeik üzenetablakok és sztringtábla-kulcsok (`CAboutBox::...`, `CWebExportNotify::...`). | Ablakos felületek, nincs betűobjektum. |

A tartomány dátumformázói közül hívást kap: `0x0098c780` (`%s %d`, 3 hely, mind a `0x007fee70`-ben) és `0x0098c670` (1 hely, a `0x007f9880`). Más dátum- vagy időformátum-szöveg (`%Y-%m-%d`, `%.2d:%.2d`, `HH:mm`) a tartomány függvényeiből nem hivatkozott. A tartományban álló `%` formátumok: `%s %d`, `%d %s`, `%s%s_f`, `%I64u`, `%s%s%s%s%s`, `%s%s\%s\%s\`, `%d` darabszámok; egyik sem dátum-idő.

**Mit csinál a `0x008014d0` és a `0x007fc7c0` (a feladat 1. része).**

- `0x008014d0` (kártyakészlet-építő): felszabadítja a régi kártyakészletet (`0x00803c10`), majd a `[this+0x3ec]` azonosító-listán végigmenve minden azonosítóra a `[this+0x2e4]` objektum 0. virtuális metódusát hívja `(azonosító, rekord, 1)` argumentumokkal; ez tölti az elem rekordját. Ezután új `0xf8` bájtos kártyarekordot kezd (`0x007fa5b0`), és a `0x00a6aa00` hívással az elem rekordjának képét **teljes téglalappal** (`-1, -1, -1, -1`) másolja a kártyarekord `+4` képébe. A kártya véletlen eltolását és irányát `rand`-ból számolja. Szöveget nem rajzol. A `[this+0x2e4]` egyetlen írója a tartományban a qshow konstruktor (`0x007fa81e`: `mov [ebp+0x2e4], ecx`), tehát az objektumot a konstruktor kapja kívülről.
- `0x007fc7c0` (rekordsáv-építő, a `0x008037e0` egyetlen hívása): törli a régi rekordokat és időket, majd a gyűjtemény elemlistáján (`[[this+0xac]+0x158]`, 0x38 bájtos elemek, darabszám `+0x15c >> 1`) végigmegy a `0x004ae4e0`-nel: ez az `index`-edik elem adatait másolja egy helyi rekordba (zár alatt, a `0x004ae600` másol). Csak azoknak az elemeknek az azonosítóját gyűjti be, amelyeknél a rekord típusmezője 1, és egy bájtos jelzője nulla (a dekompilálás szerint; a mezők jelentését nem vizsgáltam). Minden azonosítóra a `CThumbDB+0x48` virtuális tábla `+0x20` helyét hívja (ez a `0x0044f7c0`, az idő f64-ként), az idők a `[this+0x88]` tömbbe kerülnek. A `0x007fc4c0` ebből számol: az idők tömbjén a `0x0098ba30`, `0x0098b9e0`, `0x0098b550` hívásokkal egy-egy időt alakít át, a `[this+0x90]` tömbbe egy-egy összegző értéket ír az idők közötti eltérésekből; szöveget és képet nem érint. Utána minden azonosítóra: `0x004ae430(azonosító, rekord)` lekéri az elem rekordját (a `[[this+0xac]+0xc4]` objektum, a `CThumbDB` elsődleges virtuális táblájának `+0x20` helye, `0x00423300`, amely az azonosító alapján keres rekordot), `0x007fa5b0` új kártyarekordot kezd, és a `0x00a6aa00` ismét teljes téglalappal másolja az elem rekordjának képét a kártyarekord `+4` képébe. A rekord `+0` helyére az azonosító kerül. A függvény a fókuszkártya sorszámát (az `[this+4]`-gyel egyező azonosítót) a `[this+0x20]` eltolásba számolja (`[this+8] - sorszám * [this+0x30]`).
- **A kártya `+4` képe tehát az elem rekordjának másolata** (`0x00a6aa00`, `eax` = a forrás rekord, első veremargumentum = a cél kép; a forrás szélességét és magasságát a `[+8]`, `[+0xc]` adja, teljes téglalapnál a `0x009a8ca0` másolja a pixeleket). Mindkét helyen (`0x007fcca7`, `0x008015a8`) a forrás a hívás előtt a `0x004ae430`, illetve a `[this+0x2e4]` metódusa által töltött helyi rekord. Hogy ez a rekord kész bélyegképet tartalmaz-e, és honnan jön (adatbázis-gyorsítótár vagy fájlbetöltés), azt nem olvastam: a `0x00423300` (rekordkeresés a `0x00448fb0`-val, majd `0x004114e0` másolás), a `[this+0x2e4]` osztálya és a `0x00448fb0` ebben a körben nincs végigolvasva.
- Egyik sem hív szövegrajzolót vagy dátumformázót; a `0x007fc7c0` hívottjai között (`0x00401000`, `0x004ae430`, `0x004ae4e0`, `0x007fa5b0`, `0x007fc4c0`, `0x00803b50`, `0x00803c10`, `0x0097c810`, `0x0097caf0`, `0x009a8bc0`, `0x00a6aa00`, `0x00c0769f`, `_free`) nincs ilyen. A `0x00803c10` és `0x00803b50` a kártyarekord szabadítója és másolója (a `0x007fcdb3`-nál a ciklus a `+0x30`... mezőket szabadítja és a `0x009a8bc0`-t hívja); szöveget nem érintenek.

**Következtetés.**

1. **Bináris, a hatókör megjelölésével:** a `0x007f0000`-`0x00808000` tartományban a betűobjektum szövegrajzolóját (`0x00a46bb0`) összesen 7 hely hívja, mind a `0x007fee70`-ben (6) és a `0x00801cf0`-ban (1). Ezek közül egyik sem rajzolja a `YYYY-MM-DD hh:mm` alakot: a `0x007fee70` gyűjteménynevet, hónap-évet (`%s %d`) és a dátumvonal két végének hónap-évét rajzolja; a `0x00801cf0` csak a gyűjtemény nevét. A tartomány egyetlen dátumformázó hívásai a `%s %d` (3) és az `MMM d, yyyy` (1, nem rajzol). **A qshow-tartomány tehát nem rajzol teljes dátum-időt a kártyára.** A hatókör: a tartomány 247 függvénye és nyers bájtjai; a függvényhatárokon kívüli kód, a tartományon kívüli rajzolók és a függvénymutatón át hívott rajzolók nincsenek lefedve.
2. **Bináris:** a nagy kártya képe (`+4`) az elem rekordjából másolt kép (`0x00a6aa00`, teljes téglalap). A qshow-tartomány ezután nem ír szöveget erre a képre (a tartomány két rajzolója a célképre, illetve a `[this+0x46c]` képre ír, nem a kártyaképre).
3. **Következtetés a kódból, becslés nélkül:** ha a felvételen a nagy kártyán a dátum-idő látszik, a kód alapján két helyről jöhet. (a) A kártya forráskép-rekordjából, vagyis a `0x004ae430` / `[this+0x2e4]` által töltött elem rekordjából (a bélyegkép-szolgáltató oldaláról, a qshow-tartományon kívül); ennek eldöntése a `0x00423300` és a `[this+0x2e4]` osztály végigolvasását kéri. (b) A qshow-n kívüli közös rajzolóból: a OneUp UI képaláírása (`oneup/caption`, a `0x00802ec0` a `[this+0x260]` szolgáltatótól kér szöveget), amelyet a `0x008037e0` (a `qshow` és `oneup/timeline` sztringeket is használja) kapcsol a qshow-hoz. Egyik sem bizonyított, a kód csak a két helyet mutatja.

**Nyitott.**

- A `0x00423300` (rekordkeresés, `0x00448fb0`, `0x004114e0`): mit tölt a rekordba, és van-e benne kész kép vagy szöveg.
- A `[this+0x2e4]` objektum osztálya: a qshow konstruktor hívója adja át; a `0x007fa7f0` hívói és a paraméter eredete nincs végigkövetve.
- A OneUp UI képaláírás-szolgáltatója (`[this+0x260]`, virtuális tábla `+0x14`, `0x00802ec0`): milyen szöveget ad (név, dátum, időpont?).
- A felvétel (38.2.81) vizsgálata: a `2009-05-14 10:00` felirat a qshow ablakban a nagy kártyán belül van-e, vagy a OneUp UI képaláírása.
- A `0x007f1270` és a `0x007f4640` (`SendMessageA`) tartalma: ablakos segédek, nem olvastam.

**Fejlesztői átadás (csak binárisból igazolt elemek).**

| Eredeti | Teendő |
|---|---|
| A nagy kártya képe az elem rekordjának teljes másolata (`0x00a6aa00`, teljes téglalap; `0x007fcca7`, `0x008015a8`) | A kártyakép a bélyegképből készül, külön vágás nélkül; a PicasaPy-ban a kártya képforrása ugyanez legyen (átvehető, mérettől független). |
| A qshow-tartomány 7 szövegrajzolása: gyűjtemény neve, hónap-év, dátumvonal két vége (`0x007fee70`), gyűjteménynév a gyorsítótár-képre (`0x00801cf0`) | A korábbi átadások (38.2.89, 38.2.90) érvényesek; ebben a körben új tétel nincs. |
| A teljes `YYYY-MM-DD hh:mm` felirat rajzolója | Nincs: a qshow-tartományban nem létezik. Átvehető teendő nincs; a forrás a fenti nyitott pontok szerint a rekord képe vagy a OneUp UI képaláírása. |

**Új kutatási jegyjavaslat.** Nincs; a nyitott pontok a #6532 hatókörében maradnak. A következő célzott kör: `0x00423300` és a `[this+0x2e4]` osztály, valamint a OneUp UI `0x00802ec0` szolgáltatója.

#### 38.2.93 A dátum-idő felirat és a ferde csíkozás a tesztkép tartalma (#6532, 2026-11-05)

**Forrás.** A felvétel mintakészlete, a saját, gépi előállítású `minta-idorend.tar.gz` (a Colab-végrehajtó kellékei), ebből a `2009_majus/2009_majus_01.jpg`; és az `idorend-job373.mp4` 10,000 másodperces képkockája.

**Mérés.** A `2009_majus_01.jpg` 800x600-as kép: piros alapon világos, ferde csíkok, rajta fehér betűkkel két sor, `2009_majus`, alatta `1/1  2009-05-14 10:00`. A felvétel 10,000 másodperces képkockáján:

| a képkockán | mi az |
|---|---|
| a panel hátterében a nagy, halvány `...9_majus` / `2009-05-14 10:00` felirat és a ferde csíkozás | a kijelölt tesztkép nagyítva, szürkén, a panel bal szélén levágva; a betűk, a sortörés és a csíkok iránya egyezik a képpel |
| a jobb alsó színes kártyák (piros, kék, zöld) apró szövege | ugyanezek a tesztképek kicsinyítve, eredeti színben; a pirosan `2009_majus 1/1 2009-05-14 10:00` olvasható |
| a jobb felső `2009_majus` / `May 2009` | a qshow saját felirata (`0x007fee70`, 38.2.88-38.2.89) |

**Következtetés.** A teljes `YYYY-MM-DD hh:mm` felirat és a ferde csíkozás **nem a Picasa felületének eleme**, hanem a tesztkép tartalma. Ezzel lezárul a 38.2.88-38.2.92 két nyitott kérdése, és megmagyarázza, miért nem volt sem dátum-idő formázó, sem csíkozó rajzoló a qshow-kódrészben (38.2.92 leltár). A 38.2.85 „ferdén csíkozott sötét mező” és „nagy bal oldali dátumfelirat” megfigyelése tehát a háttérbe tett kijelölt képet írta le.

**A háttérkép bináris útja (olvasat, a 38.2.90 mellékleleteiből).** A `0x00802130` a `[this+0x46c]` képet szürkévé alakítja, a `0x008001c0` a `[this+0x444]` és a `[this+0x46c]` képet keveri, a `0x00802230` a `+0x46c`-t a `+0x444`-be másolja. Ez összhangban van azzal, hogy a háttér a kijelölt kép szürke, halványított változata; hogy a `+0x46c` a kijelölt elem képéből töltődik-e, azt a kód még nem mutatta meg.

**Nyitott.** A `[this+0x46c]` kép kitöltője (a kijelölt elem képe-e), a halványítás mértéke, és a `+0x5f8`, `+0x620` kép tartalma.

**Fejlesztői átadás.** A PicasaPy Időrend-nézete **ne rajzoljon** saját dátum-idő feliratot és csíkozott hátteret: ezek a mérésben a kép tartalmából jöttek. Binárisból igazolt elem ebben az alszakaszban nincs; a háttérkép szürkítése és keverése a fenti címeken olvasat.

**Módszertani tanulság.** Mielőtt egy felvételen látott elem rajzolóját a programfájlban keressük, a mintakészlet képeinek saját tartalmát kell megnézni: öt Ghidra-kör kereste a tesztképbe írt szöveg rajzolóját.

#### 38.2.94 A háttérkép: szürkítés, automatikus javítás, világosító görbe és ráterített fedőkép (#6532, 2026-11-05)

**Forrás.** Helyi, indextől független pásztázás a teljes `.text`-en (capstone, minden `[reg+eltolás]` és közvetlen érték, ahol az eltolás `0x5f8`, `0x620`, `0x46c`, `0x444`), utána utasításszintű olvasás. Dekompilátum nem kellett.

**a) A `+0x5f8` és a `+0x620` kép üres marad.** A teljes programban ezekre az eltolásokra a qshow-ból csak a konstruktor (`0x007fa7f0`, `0x007fab2c`, `0x007fab5b`: üres, 0x0-s tároló, `0x009a8a30`), a felszabadító (`0x007fb5a0`) és a rajzoló (`0x007ffc90`) hivatkozik. A qshow-tartományban (`0x007f0000`-`0x00808000`) nincs indexelt (`[reg+reg*k+eltolás]`, `0x500`-`0x760` közötti eltolással) és nincs `0x28`-as szorzású hozzáférés, a `0x5f8`/`0x620` közvetlen értékként sem szerepel. Az erőforrás-betöltő (`0x007fb210`) a `+0x530`, `+0x558`, `+0x5a8`, `+0x5d0`, `+0x580`, `+0x6c0`, `+0x6e8`, `+0x710`, `+0x738` tárolót tölti, a `+0x5f8`-at és a `+0x620`-at nem. A `0x009a8a30` 0 szélességnél nem foglal (`0x009a8a4b`), és a rajzoló `0x009ab690` vágója (`0x009aaae0`) üres téglalapnál kihagyja a rajzolást. **Következtetés:** a két kép a mért Picasában üres, a `0x007ffc90` ezeknél nem rajzol semmit. Átvehető teendő nincs.

**b) A `+0x46c` a teljes képkocka, nem a háttér forrása.** A `0x008001c0(this, &this[0x46c], téglalap)` a teljes jelenetet ebbe a képbe rajzolja (hívói: `0x007fb86b`, `0x00802ab6`, `0x00802b06`); a `0x00801cf0` a gyűjtemény nevét is ide írja. A `0x00802230` frissítő előbb a régi kockát a `+0x444`-be menti (`0x00802516`-`0x00802525`), majd a `[this+0x2e4]` képszolgáltató virtuális `+8` hívásával (`0x008023ad`-`0x008023f8`) kért képet a kocka közepére másolja (`(+0x474 - szélesség) / 2`, `(+0x478 - magasság) / 2`, `0x0080255b`-`0x0080259f`, `0x009aabf0`).

**c) A szürke, fakított háttér: a `0x00802180`.** A `0x00802230` második (bájt) argumentuma dönt: ha nem 0, a másolás után a `0x00802180` fut (`0x008025a4`-`0x008025af`). A hívóhelyek argumentuma:

| hívóhely | függvény | második argumentum |
|---|---|---|
| `0x007fb56c` | `0x007fb540` (ha `[this+0x51a]` nem 0) | 1 |
| `0x007fda4f` | `0x007fda00` (a megnyitás, a mutatót is elrejti) | 1 |
| `0x00801178` | `0x00801130` (szünet-ág) | 0 |
| `0x00801d05` | `0x00801cf0` (gyűjteménynév) | 0 |
| `0x008026e9` | `0x00802630` (a vetítés léptetője: a `+0x3f4` indexet lépteti, a sor végén a `0x007fb820` vagy a `0x007fda00`) | 0 (dekompilátum: `FUN_00802230(this, 0)`) |

A `0x00802180` lépései, sorrendben:

| lépés | cím | mit csinál |
|---|---|---|
| 1. szürkítés | `0x0080218f` → `0x00802130` | minden képpont `G * 0x10101`: a zöld bájt kerül mindhárom csatornába, az alfa-bájt 0 lesz (`0x00802152`-`0x0080215c`) |
| 2. automatikus javítás | `0x008021b1` → `0x00407a20` (`Preferences/CarefulEnhance`), `0x008021cb` → `0x009db610` | ugyanaz a vágó-nyújtó, mint a `enhance` szűrőé: a `-1,0` jelző miatt `keverés = 0,30`, a `CarefulEnhance` beállítással 252-es felső korlát (`filters-decoded.md`) |
| 3. világosító görbe | `0x008021d0`-`0x008021e1` → `0x00aa40a0(3,0, 0)` | 8 bites gamma-tábla, kitevő `1/3`: `LUT[i] = rint(255 * (i/255)^(1/3))`, mindhárom csatornán (a táblaépítőt lásd `picasa-native-filter-workers.md` 5.3/b) |
| 4. fedőkép | `0x008021f2`-`0x00802207` → `0x009ab410(&this[0x46c], &this[0x648], teljes)` | a `+0x648` képet a teljes kockára keveri |

A `+0x648` a `0x007fb210` betöltőben készül: a `layer:overlays/overlay` erőforrást (`0x00cbd3e8`, 640x480 RGBA, alfa 179-255, 38.2.85) a qshow ablakméretére méretezi (`0x009a9c90` a `[this+0x2d0]-[this+0x2c8]` szélességgel, `0x007fb4bb`-`0x007fb4c4`), majd újramintavételezi (`0x00a42c20`).

**Következtetés.** (1) Bináris: megnyitáskor a háttér a képszolgáltatótól kért kép a kocka közepén, szürkítve (zöld csatorna), `enhance`-szerűen nyújtva (0,30), `1/3` kitevőjű görbével erősen világosítva, és rajta az ablakméretre nyújtott `overlays/overlay` fedőkép. (2) Bináris: szünetkor, lapozáskor (`0x00802630`) és gyűjteménynév-frissítéskor a frissítő ezt a fakítást nem futtatja. (3) Kizárva: a `+0x5f8`/`+0x620` mint háttérforrás (üres tárolók). (4) Nem igazolt: hogy a képszolgáltató a kijelölt elem képét adja; a 38.2.93 képkockája ezt mutatja, a `[this+0x2e4]` osztály virtuális `+8` célja nincs feloldva.

**Fejlesztői átadás.**

| Eredeti | Teendő a PicasaPy-ban |
|---|---|
| Háttér: a kép középre, szürkítés a zöld csatornából, `enhance`-nyújtás 0,30 keveréssel, gamma `1/3` (`0x00802180`) | A `TimelinePanel.qml` egyszínű `#8a888b` alapja helyett ezt a háttérképet kell rajzolni. A meglévő elemek: `render/ops_levels.py::apply_enhance` (a `0x009db610`), `render/native_tone.py::native_gamma_lut` (a `0x00aa40a0`). |
| Fedőkép: `overlays/overlay`, ablakméretre nyújtva (`+0x648`) | Az eredeti erőforrás nem másolható; saját rajzolással kell újraalkotni (ovális sötét felület, halvány külső ív, alsó sáv, 38.2.85), az átlátszóság mért 179-255-ös tartományát megtartva. |
| `+0x5f8`, `+0x620` | Nincs teendő: üresek. |

**Nyitott.** A `[this+0x2e4]` képszolgáltató virtuális `+8` célja (melyik elem képét adja, milyen méretben; a méretkérés `f32 [0xd35808]`-ból jön). A 38.2.93 nyitott pontjai közül a `+0x46c` kitöltője és a halványítás mértéke ezzel lezárva.

#### 38.2.95 A `[this+0x2e4]` képszolgáltató forrása (#6532, 2026-11-05)

**Forrás.** Utasításszintű olvasás: a qshow konstruktora (`0x007fa7f0`) és egyetlen hívója, a `0x008037e0`, valamint ennek hívója, a `0x005e8a70` (a bélyegkép-nézet vetítésindítója); teljes `.text`-pásztázás a `+0x2e4` eltolásra.

**Mérés.** A qshow-tartományban a `[this+0x2e4]` mezőt egyetlen utasítás írja: `0x007fa81e` a konstruktorban. A konstruktor egy paraméterrekordból tölt (`edi`): `+0xc` → `[this+0x2e0]`, `+0x10` → `[this+0x2e4]`, `+8` → `[this+0x2e8]` (`0x007fa812`-`0x007fa827`). A rekordot a `0x005e8a70` építi a veremben (`esp+0x64`), és a `0x005e9787`-nél adja a `0x008037e0`-nak:

| rekordmező | érték | utasítás |
|---|---|---|
| `+0` | bájt (`al`) | `0x005e96f1` |
| `+1` | bájt, a hívó `[ebp+0xc]`-je | `0x005e9706`-`0x005e9713` |
| `+4` | `[[ebx+0xeac]+0x3c0]` | `0x005e96eb`-`0x005e9709` |
| `+8` | `&ebx[0x27c]` (→ qshow `+0x2e8`) | `0x005e971b`, `0x005e973d` |
| `+0xc` | `&ebx[0x270]` (→ qshow `+0x2e0`) | `0x005e9721`, `0x005e9741` |
| `+0x10` | `[ebx+0x2bc] + 0x4c`, vagy 0, ha `[ebx+0x2bc]` üres (→ qshow `+0x2e4`) | `0x005e970d`-`0x005e9750` |
| `+0x24`, `+0x28` | `0x400`, `0x300` (1024×768) | `0x005e9727`, `0x005e9732` |

**Következtetés.** (1) Bináris: a vetítés képszolgáltatója a bélyegkép-nézet `[+0x2bc]` objektumának `+0x4c`-n beágyazott felülete; a `0x00802230` ennek virtuális `+8` hívásával kéri a háttérképet (38.2.94 b). (2) Nem igazolt: hogy a `[+0x2bc]` objektum melyik osztály, így az sem, hogy a kért kép a kijelölt elem bélyegképe vagy teljes képe. A 38.2.93 képkockáján a háttér a kijelölt kép, ez mérés.

**Fejlesztői átadás.** A #6577 a kijelölt fotó bélyegkép-szolgáltatójából kéri a háttérképet; a fenti lelet ezt nem cáfolja, és a 1024×768-as rekordmező miatt a forrás felbontása a panelnél nagyobb lehet. Új teendő nincs.

**Nyitott, a következő felvehető irány.** A bélyegkép-nézet `[+0x2bc]` mezőjének írója (a `0x005e`-tartományban `mov [reg+0x2bc], reg` alakú utasítás), és az ott tárolt objektum vtáblájának `+0x4c` alatti beágyazott felülete.

#### 38.2.96 A körhinta lépésköze, a fókusz kezdőhelye és a lap magassága (#6595, 2026-11-06)

**Kérdés.** A 38.2.24 §1 szerint a kártyák `t_i = i·S + O` paraméteren állnak a `0x007fbab0` görbén, de az `S` írója nyitott volt (B1). A tulajdonos tíz teljes képernyős felvétele (1920×1080, 2009-2026 közötti gyűjtemények, a tulajdonos helyi mappájában, a repóba nem kerül) azt mutatja, hogy minden gyűjtemény egy köteg a görbén, a régebbiek balra-hátra kicsinyednek, az újabbak jobbra állnak, és lapozáskor az egész sor átúszik.

**Módszer.** A út: a qshow-kódterület (`0x007f9000`-`0x00804000`) függvényeinek indexfüggetlen, capstone-os bejárása a `+0x30` eltolású írásokra (`fst*`/`mov`, a veremre mutatók nélkül); egyetlen találat: `0x007fba9a`. Ezután a `0x007fb9f0` és a `0x007fbd90` vége utasításonként. B út: a konstansok nyers PE-olvasása.

**1. Az `S` írója: a sáv konstruktora, `0x007fb9f0` - megerősített.** A függvény az `esi` objektum (a qshow `+0x2f8` sávja, P) mezőit nullázza (`+0x40`, `+0x50`…`+0x7c`, `+0x80`…`+0xbc`, `+0x20`, `+0x18`, `+0x10`), a `[P]`-be `-1`-et ír, majd:

| utasítás | hatás |
|---|---|
| `0x007fba94` `fld qword [0x00cf4e30]`, `0x007fba9a` `fstp qword [esi+0x30]` | `S = 0.04999999888241291` (az f32 `0.05` dupla pontosságú alakja) |
| `0x007fba9d` `fld1`, `0x007fba9f` `fstp qword [esi+0x28]` | `Z = 1.0` (a kártyalépték szorzója) |
| `0x007fbaa2` `call 0x007fbd90` | a `runtime\bezier.txt` betöltése |

**2. A fókusz kezdőhelye: `0x007fbd90` vége - megerősített.** A négy vezérlőpont beolvasása után (`0x007fbe53`-`0x007fbe70`) a `0x007fbe74` hívja a `0x007fbce0`-t (a görbe azon `t*` paramétere, ahol az x a legközelebb van `0.666`-hoz), majd az eredményt `0x007fbe87` `fst dword [ebx+8]` a `P+8`-ba, `0x007fbe8a` `fstp qword [ebx+0x20]` az `O`-ba írja. A `0x007fc010` korlátai (`O ≤ [P+8]`, `O ≥ [P+8] - (n-1)·S`, 38.2.24 §2) így azt jelentik: induláskor és a lista elején az első gyűjtemény áll a fókuszban (x ≈ 0.666), a többi jobbra; a lista végén az utolsó áll ott, a többi balra. A 38.2.61 vezérlőpontjaival a bináris 0,0001-es rácsán `t* = 0.9358`.

**3. Egyezés a felvételekkel - mérés.** A panel bal felső sarkához mért, 480 px magas lapon a kötegek egymást 0,05-ös paraméterlépésben követik: a fókuszkötegtől balra eső kötegek helye a `t* - k·0.05` görbepontok sorát, a jobbra esőké a `t* + k·0.05` pontokét követi; a fókuszköteg vízszintes helye a lap szélességének 0,66-a, ahogy a `0.666`-os fókuszfeltétel adja. Az első felvételen (az első gyűjtemény) a fókusz mellett csak jobbra van köteg, az utolsón (Legutóbb frissítve) csak balra; ez a 2. pont korlátaival egyezik. A felvételek egy része két háttér keverékét mutatja: a gyűjteményváltáskor a háttér átúszik.

**4. A lap mérete - mérés, nem bináris.** A tulajdonos 1920×1080-as felvételein az Időrend lapja 852×480 px a fekete képernyő közepén; a korábbi job-217 1280×1024-es felvételén 600×480 px. Mindkettő 480 px magas, és a szélessége `480 · képernyőszélesség / képernyőmagasság`. A lapméretet kiszámoló utasítást ebben a körben nem kerestem meg. **Termékdöntés (tulajdonos, 2026-11-05):** a PicasaPy Időrendje a teljes képernyőt töltse ki; ehhez a 480 px magas logikai lapot egyenletesen a képernyő magasságára nagyítjuk, így a képarány az eredetié marad, és nincs fekete sáv.

**Következtetés.** (1) Bináris: `S = 0.05`, `Z = 1.0` a `0x007fb9f0`-ból, `O = P+8 = t*` a `0x007fbd90`-ből; ezzel a 38.2.24 B1 lezárva. (2) A teljes körhinta-elrendezés (hely, lépték, átlátszóság, láthatóság, korlátok, fókusz, animátor) binárisból adott; a megvalósítás a #6595. (3) Mérés: a lap 480 px magas, szélessége a képernyő arányát követi.

**Nyitott, a következő felvehető irány (lezárva: 38.2.98).** A lapméret kiszámítása a binárisban: a `0x00801f50` `GetClientRect` utáni `0x009b49c0(&rect)` elrendező hívása, ahol a 480-as konstans (`0x1e0`) vagy a magasságarány várható.

#### 38.2.97 A vetítés legalább 640 px-es fotóforrást kér (#6604, 2026-11-06)

**Forrás és módszer (utasításszintű olvasat, a helyi `Picasa3.exe`-ből).** A `0x00802230` a `0x008023ad`-`0x008023f8` között a `[this+0x2e4]` képszolgáltató vtábla `+8` slotját hívja `(rekord, kimenet, méret)` argumentumokkal; a méret `trunc([0x00d35808])`, ahol az f32 konstans `2276.5557` (a `0x00d35808`-at a független memóriaeltolás-pásztázás szerint 15 utasítás csak olvassa, író nincs). A szolgáltató a `CThumbDB` `+0x4c`-n beágyazott felülete: a `0x00415790` és a `0x00417770` konstruktor a `[this+0x4c]`-be a `0x00c820a8` vtáblát írja (`0x0041580b`, `0x00417786`), amelyet az RTTI-index `CThumbDB::vftable` néven azonosít; a `+8` slot a nyers PE-adat szerint `0x00424b10`.

**Mért küszöb.** A `0x00424b10` a kis és közepes méretű bélyegképet legfeljebb 256, illetve 512 px-es kérésekre használja. Nagyobb kérésnél a küszöb `kért_méret · 144 >> 9`; a `2276`-ra csonkolt kérés eredménye **640 px**. Előbb a `+0x2330`, majd a `+0x2284` gyorsítótárat vizsgálja. Ha mindkét kép mindkét oldala a küszöb alatt marad, a `0x006a0b10` háttérkéréssel készítteti el a nagyobb képet (`0x00424b63`-`0x00424bd9`).

**Következtetés.** A teljes képernyős Időrend háttérforrása legalább 640 px hosszabb oldalú kép a fotóból; a 256 px-es rácsbélyegkép felnagyítása nem megfelelő forrás. A kisebb eredeti fotót nem lehet valódi részlettel 640 px-re bővíteni.

**Fejlesztői átadás.** A PicasaPy Időrend háttérszolgáltatója a fotófájlból olvasson legalább 640 px-es forrást, ne a rács 256 px-es lemez-cache-éből. A #6577 szürkítési, automatikus javítási, gamma- és fedőréteg-lánca változatlan marad; a forrás előállítása a már aszinkron QML-kérésben történik, a kész háttér pedig az Időrend LRU-jába kerül.

#### 38.2.98 A lap méretét a `0x007fa730` számolja: az Időrend mindig 480 px magas, képernyőarányos lapot kap (#6532, 2026-11-06)

**Kérdés.** A 38.2.96 4. pontja a 480 px magas, `480 · W / H` széles lapot csak a felvételekből mérte; a lapméret kiszámítása a binárisban nyitott volt.

**Forrás és módszer (utasításszintű olvasat, a helyi `Picasa3.exe`-ből, capstone).** A `0x00801f50` rajzolás előtti elrendezője a `[this+0x3c4]` képobjektum `+8`/`+0xc` mezőjét (szélesség, magasság) és az ablak téglalapját adja a `0x009b49c0`-nak (`0x00801fbb`-`0x00801fea`); ez a belső téglalapot a külső közepére igazítja (`(külső - belső) / 2`), méretet nem számol. A `[this+0x3c4]` kép a `0x00800a30`-ban a `[this+0x2c8]` téglalap méretével jön létre (`0x00800b99`-`0x00800ba5`, `0x009a9c90`). A `[this+0x2c8..0x2d4]` mezőt a qshow-tartományban (`0x007f9000`-`0x00805000`, indextől független pásztázás) csak a `0x007fa3d0` nullázza és a `0x007fa4c0` írja; ez utóbbi a `ytDDrawable` (`0x00cbd564`) és a `QDrawable` (`0x00cbd66c`) vtábla `+0x44` slotja, vagyis a rajzolható elem téglalap-beállítója. A 480-as konstans (`0x1e0`) a qshow-tartományban egyetlen függvényben fordul elő: `0x007fa730`.

**A `0x007fa730` - megerősített.** Hívói: `0x008037e0` (`0x00803883`, a vetítés indításakor) és `0x00801270` (`0x0080146e`).

| utasítás | hatás |
|---|---|
| `0x007fa73c`-`0x007fa746` | `GetSystemMetrics(1)` és `GetSystemMetrics(0)`: a képernyő `H` magassága és `W` szélessége; a képernyő téglalapja `(0, 0, W, H)` |
| `0x007fa761`, `0x007fa767` | alap: `640 × 480` (`0x280`, `0x1e0`) |
| `0x007fa76d`-`0x007fa77c` | ha a jelzőbájt **0**, az alap a teljes képernyő: `W × H` |
| `0x007fa77e`-`0x007fa7af` | `arány = W / H`; a lap szélessége `round(alap_magasság · arány)` |
| `0x007fa7cd`-`0x007fa7d8` | a lap téglalapja `(0, 0, round(alap_magasság · W / H), alap_magasság)` |
| `0x007fa7c1`, `0x007fa7dc` | `[0x00d34040] = arány / 1.3333333` (a `0x00cf4908` dupla pontosságú konstans) |

**A jelző forrása, `0x008037e0` - megerősített.**

1. `0x008037f8`-`0x0080382a`: a `HKEY_CURRENT_USER` alatti `Preferences\BigSlideshow2` DWORD (`0x00407a20` és `0x004019b0`; alapérték 1, `0x0080380d`). A jelző 1, ha az érték 0.
2. `0x00803825`-`0x00803839`: a jelző 1, ha a `[0x00d33958]` nem 16 és nem 32. A `[0x00d33958]`-at a `0x0097e030` írja: `GetDeviceCaps(hdc, 12)`, azaz a képernyő színmélysége bit/képpontban.
3. `0x0080383e`-`0x00803849`: a jelző 1, ha a paraméterrekord `+1` bájtja nem 0. Ez a bájt a vetítésindító `0x005e8a70` második paramétere (38.2.95). A hívóhelyek közül a `thumbui/timelinebutton` ága `1`-et ad (`0x005da79e`, `0x005da7ab` `push 1`), a `thumbui/sbutton` (diavetítés) ága `0`-t (`0x005da733`, `0x005da740` `push 0`).

**A `Ctrl+O` váltó - megerősített, rejtett.** A `0x00801270` a vetítés `WM_KEYDOWN` (`0x100`) kezelője (`Esc` `0x1b`, nyilak `0x25`-`0x28`, szóköz `0x20`). Az `O` (`0x4f`) ága `GetKeyState(VK_CONTROL)` mellett átbillenti a `[this+0x2d8]` jelzőt, és újraszámolja a lapot (`0x0080143b`-`0x0080146e`). Az ágat, a `Ctrl+F` (`0x46`) és a `Ctrl+B` (`0x42`) ágával együtt, a `[0x00d67849]` bájt kapuzza; ezt csak a `0x005760e0` (`0x00576419`, állandó 1) és a `0x00a52890` (`0x00a52e66`) írja. Hogy ez a kapu mikor nyit, nem olvastam ki.

**Következtetés.** (1) Bináris: az Időrend gombjáról indított vetítés jelzője mindig 1, ezért a lap `round(480 · W / H) × 480` méretű, és a `0x009b49c0` a képernyő közepére teszi. Ez egyezik a 38.2.96 4. pontjának mérésével: 1280×1024-en a számolt 600×480 pontosan a mért, 1920×1080-on a számolt 853×480 a felvételen mért 852×480-tól 1 px-re van; a 4. pont ezzel lezárva. (2) Bináris: a sima diavetítés (`thumbui/sbutton`) alapbeállítással (`BigSlideshow2 = 1`, 16 vagy 32 bites színmélység) a teljes képernyőt kapja. (3) Termékdöntés (tulajdonos, 2026-11-05): a PicasaPy Időrendje a 480 px magas logikai lapot a képernyő magasságára nagyítja (38.2.96); a fenti leképezés ezt nem változtatja, a `Ctrl+O` rejtett váltó nem cél.

**Nyitott.** A `[0x00d67849]` kapu jelentése (a `0x005760e0` és a `0x00a52890` hívási feltétele); a termékre nincs hatása.

#### 38.2.99 A háttérkép a qshow aktuális képazonosítóját követi (#6532, 2026-11-07)

**Kérdés.** A 38.2.94/95 nyitott pontja az volt, hogy a háttérhez hívott képszolgáltató melyik képet kapja, és változik-e a háttér a gyűjtemény lapozásakor.

**Forrás és módszer.** A helyi `Picasa3.exe` célzott, utasításszintű diszasszemblálása (`annot_disasm.py`) a `0x008018a0`, `0x008014d0`, `0x00802230` és `0x00424b10` függvényekre; független ellenőrzésként a korábban elkészült Ghidra-kimenetek (`2026-10-21-idorend-8.txt`, `2026-10-17-qshow-2.txt`, `2026-11-05-idorend-6532-kartyakeszlet.txt`); valamint a meglévő job373 videó. A videófolyam metaadata: 1280×1024, 15 képkocka/s, 1500 képkocka, 100,000 s. A képkockákat a teljes videó dekódolása után, a zérus alapú sorszám alapján választottam ki (FFmpeg `select`), így nem a közeli kulcsképkocka gyors pozicionálásából származnak. A másolatot és a képkockákat a munkafa ideiglenes `.bt/` könyvtárából a vizsgálat után törlöm.

**Bináris adatút.**

1. A gyűjteményváltó `0x008018a0` a `[this+0x50c]` gyűjteményindex változásakor újraépíti a `[this+0x3ec]` azonosítólistát. A régi listát felszabadítja, a `[this+0x3f0]` elemszámot újraindítja, a `[this+0x3f4]` képindexet nullázza (`0x008018e5`-`0x0080190d`), majd a kiválasztott elemek azonosítóit a listába írja (`0x00801ba6`-`0x00801bc4`). A lista forrásának és szűrésének részleteit a 38.2.92 tartalmazza.
2. A kártyakészítő `0x008014d0` ugyanezt a `[this+0x3ec]` listát járja: az aktuális ID-t a `[this+0x3ec][i]` kifejezésből olvassa (`0x00801570`-`0x0080157a`), a `[this+0x2e4]` szolgáltató virtuális slot `+0` hívásával tölti az elemrekordot, majd ebből kártyarekordot épít. A gyűjteményváltó a kártyakészítőt a `0x00801c95` címen hívja.
3. A háttérfrissítő `0x00802230` előbb ellenőrzi, hogy a `[this+0x3f4]` index a `[this+0x3f0] >> 1` elemszámon belül van-e (`0x0080227d`-`0x00802299`). Érvényes indexnél az ID-t a `[this+0x3ec][this+0x3f4]` helyről veszi (`0x008022ba`-`0x008022c0`). Ha a `[this+0x3c1]` jelző nem nulla, ezt az ID-t a `[this+0x2e4]` objektum `+8` virtuális slotjának adja át, a `0x00d35808` f32 konstansból csonkolt 2276-os méretkéréssel (`0x00802385`-`0x008023f8`). A szolgáltató a CThumbDB beágyazott `+0x4c` felülete; a `+8` slot `0x00424b10` a 2276-os kéréshez `2276 × 144 >> 9 = 640` pixeles forráságat választ (38.2.95, 38.2.97). A kapott kép a régi képkocka `+0x444` mentése után a jelenet `+0x46c` képébe kerül; a `0x00802180` tónuslánc csak a második argumentum nem nulla értékén fut (`0x00802516`-`0x008025af`; 38.2.94).
4. A `0x008018a0` nullázása és a `0x00802230` ID-olvasása ugyanarra a listára/indexre mutat. A meglévő Ghidra-kimenet ezt külön reprezentációban is mutatja: `2026-10-21-idorend-8.txt` 552-563. és 680-725. sora a lista újraépítését, indexnullázását és kártyakészítő-hívását; `2026-10-17-qshow-2.txt` 1725-1776. sora a lista/index beolvasását és a háttér-szolgáltató meghívását tartalmazza.

**Videómérés.** A beágyazott nagy kép saját dátumfelirata és a jobb felső gyűjteményfelirat alapján:

| időpont | jobb felső gyűjtemény | a nagy háttérképen olvasható tartalom |
|---:|---|---|
| `n=91` (91/15 s) | `2009_majus` / `May 2009` | `2009_majus`, `2009-05-14 10:00` |
| `n=267` (17,800 s) és `n=300` (20,000 s) | `2014_november` / `November 2014` | `2014_november`, `2014-11-02 15:30` |
| `n=360` (24,000 s) | `2019_marcius` / `March 2019` | még `2014_november`, `2014-11-02 15:30` |
| `n=420` (28,000 s) | `2019_marcius` / `March 2019` | `2019_marcius`, `2019-03-08 09:15` |

**Következtetés.** A bináris megerősíti, hogy gyűjteményváltáskor a képindex 0-ról indul, a háttérfrissítő pedig a gyűjtemény ID-listájának aktuális indexű képét kéri le. A job373 videóban a háttér a kiválasztott gyűjtemény képéhez igazodik; a 24,000 s-os képkockán a régi háttér még látszik, a 28,000 s-oson az új. Ez megfelel a 38.2.94-ben igazolt régi/jelenlegi képkockarétegnek, nem bizonyít külön, rögzített háttérképet. Az egyes átmeneti képkockák pontos belső állapota és időtartama ebből a mintavételből nem állapítható meg.

**PicasaPy-összevetés.**

| Eredeti Picasa | Jelenlegi PicasaPy | Teendő |
|---|---|---|
| Gyűjteményváltáskor `+0x3f4 = 0`, háttérhez `+0x3ec[+0x3f4]` képet kér; 2276 méretkérésből a CThumbDB legalább 640 px-es forrást szolgáltat (`0x008018a0`, `0x00802230`, `0x00424b10`). | A `TimelinePanel.qml` az aktuális és előző gyűjtemény `photos[0]` elemét használja háttérként (34-37. sor), két `timelinebackground` képréteggel (46-80. sor). A `timeline_background.py` 640 px-es forrásméretet kér (38. sor), az eredeti fotót dekódolja (259-310. sor), majd zöldcsatornás szürkítést, enhance-t, 3-as gamma-t és saját rajzú fedőképet alkalmaz (72-79., 91-211. sor). | A háttér ID-választása gyűjteményváltáskor megfelel az eredeti 0. indexének; a 38.2.94 és 38.2.97 háttér-forrás/tónus teendője a jelenlegi forrásban már teljesül. Ehhez az alrészhez új fejlesztői jegy nem indokolt. |

**Bizonyítottsági fok: megerősített, a fenti szűk kérdésre.** A helyi utasításszintű diszasszemblálás és a korábban készült Ghidra-dekompilálás egyezik a lista/index/szolgáltató útvonalában. Ettől függetlenül a videómérés a gyűjteményváltás után a háttérben megjelenő képet a jobb felső gyűjteményfelirattal összeveti. A videó köztes, 24,000 s-os képkockája korlátozza az időzítési következtetést, de nem cáfolja a végállapot egyezését.

**Cáfoló kísérlet.** Azt a feltevést próbáltam megcáfolni, hogy a háttér a nyitáskor kapott első képen marad. A 17,800 s-os és 28,000 s-os képkockákon a háttérfelirat rendre a 2014-es, majd a 2019-es gyűjtemény képére vált, tehát a fix háttér hipotézis megdől. Ellenőrzésként a kódút ugyanazzal az ID-mércével újraolvasható: a `0x00802230` az arg2=0 ágban is kiolvassa a listából az aktuális ID-t és lekéri a képet; csak a `0x00802180` tónuslánc feltételes (`0x008025a4`-`0x008025af`). A régi kép elmentése a `+0x444` mezőbe és a jelenetkeverő a korábbi réteg jelenlétét magyarázza (`0x00802516`-`0x00802525`, `0x008001c0`; 38.2.94).

**Nyitott.** A videó nem mutat minden köztes animációs állapotot, ezért a régi és új háttér rétegarányának képkockánkénti függvénye és időtartama továbbra sincs binárisból és pontos mérésből összekötve; megszerzéséhez ugyanabban a Picasa-futásban időbélyegzett képkocka és a `[this+0x3f4]`, `+0x444`, `+0x46c` mezők egyidejű rögzítése kell. Ezen az adatúton meglévő Ghidra-kimenet van, ezért ugyanerre a kérdésre új dekompilációt nem kérek. A #6532 teljes „Kész, ha” feltételei továbbra sem tekinthetők lezártnak: a korábbi szakaszok egyéb nyitott vezérlő-, időzítési és forráshalmaz-pontjai külön megmaradnak; a megvalósítási jegyet a hívó nyithatja meg.

**Checkpoint.** Az adatút, a Ghidra-ellenőrzés, a job373 képkockamérés és a PicasaPy-forrásösszevetés rögzítve a `.codex-jelentes.md`-ben (2026-11-07).

#### 38.2.100 A háttérréteg-keverés időalapja és a `SimpleSlideshow` ágai (#6532, 2026-11-07)

**Kérdés és hatókör.** A 38.2.99-ben nyitva maradt régi/új háttérképréteg képkockánkénti progressziója. Ez a szakasz a helyi 3.9.141.259-es bináris statikus modelljét rögzíti; nem állítja, hogy a job-373 felvétel futása ugyanazokat a Preferences-értékeket használta.

**A beállítás és az időalap.** A qshow konstruktor (`0x007fa7f0`) a `SlideshowEffectTime` kulcsot a `Preferences` szakaszhoz és a `+0x760` objektumhoz kapcsolja; a beállítás-építőnek átadott alapértelmezett egész `3` (`0x007facd3`, `0x007facdb`-`0x007facf2`). A numerikus olvasó `0x004019b0`. A `0x008001c0` ezt kéri le (`0x00800255`-`0x0080025d`): nulla értéknél `p=1`; máskülönben a `+0x520` időbélyeg óta eltelt időt elosztja a beállítással (`0x00800266`-`0x00800295`). A `0x009a51b0` a `QueryPerformanceCounter` értékéből és a `QueryPerformanceFrequency` gyorsítótárazott reciprokából másodpercet számol; a két import a `0x00921a92` és `0x00922404` címen azonosítható. A `0x00802230` képkocka-frissítő az új kép beállítása után QPC-t ír a `+0x520` mezőbe (`0x008025b8`-`0x008025cf`). A `p` ezért a frissítés óta eltelt QPC-másodperc és a `SlideshowEffectTime` hányadosa.

**Progresszió és mód.** A `0x008001c0` a `SimpleSlideshow` beállítást 1-es alapértékkel olvassa (`0x00800297`-`0x008002be`). Jelölje `t` a `+0x520` óta eltelt QPC-másodpercet, `T` a `+0x760`-ból olvasott értéket. Ha `T=0`, a kód közvetlenül kész progressziót állít be. Egyébként `p=t/T`.

- `SimpleSlideshow=1` esetén az eredeti előbb `p=min(max(1.5·p,0),1)` értéket képez, majd a `0x0072df60`-ban is használt nemlineáris görbe beágyazott változatát számolja: `y=8p`, `g(y)=y-1+E(-y)` ha `y<1`, különben `g(y)=a+(1-a)·(1-E(-(y-1)))`, ahol `a=E(-1)`; a kimenet `K·g(y)`, `K=1/g(8)`. A konstansok címei: `0x00d34128=1,5`, `0x00c7ea10=8`, `0x00cf3ed0=-1`, `0x00c7e328=1`; a normalizálót `0x009e5ac0` számítja. Az `E` hívási útja `0x0040eac0` → `0x00c29c6c`, amelynek CRT-exponenciális működését a 38.2.24 §1 és §B8 már levezette. A `0x0072df60` meglévő külön függvénye és a `0x008001c0` beágyazott kódja ugyanazt a görbealakot adja.
- `SimpleSlideshow=0` esetén a pozitív `p` 1-nél felülről korlátozódik; ez az ág a `0x007fff30`-ban két külön transzformációs leírót ír a `+0x4bc` és `+0x4e4` mezőkbe, majd a `0x00aa6180` kompozitort hívja (`0x008004f9`-`0x00800546`). A `SimpleSlideshow=1` közvetlen képpontkeverő ága a `0x009dc040`-et hívja (`0x0080046c`-`0x008004f7`), transzformációs leírók nélkül.
- Mindkét mód a progressziót `alpha=trunc(256·p)` egész értékre alakítja és 256-nál korlátozza; a `+0x519` jelző 1, amíg az érték 256 alatt van (`0x0080040a`-`0x00800460`). Az előző képkocka `+0x444`, az aktuális `+0x46c`. A `0x009dc040` a régi képet első, az aktuálist második pixelforrásként kapja: `a=max(alpha-1,0)`, majd minden 8 bites csatornára `(régi·(255-a)+aktuális·a)>>8`. A `0x00aa6180` a `SimpleSlideshow=0` ágban a két forrást a két saját transzformációs leírójával dolgozza fel, majd ugyanezt a pixelkeverőt hívja.

**Következmény a névleges alapértékre.** Ha a futás a konstruktor `T=3` alapértékét és a `SimpleSlideshow=1` alapértékét használja, a `1,5`-ös skálázás miatt a görbe bemenete 1-nél telítődik, amikor `t=2` másodperc. Ez a binárisból feltételesen levezetett clamp-idő; nem a job-373 futásidejű Preferences-értéke és nem a videón mért látható átmenet időtartama.

**Videó és PicasaPy.** A korábbi job-373 képkockamérés 1,400, illetve 1,467 másodperces látható képcserét rögzített (38.2.85, 226-247. és 344-366. képkocka). Ezek a látható változásablakok nem rögzítik a Picasa futásidejű `SlideshowEffectTime` vagy `SimpleSlideshow` értékét, és nem mérik a `+0x520`-hoz viszonyított belső progressziót. A helyi `meroadat.tar`-ban nincs job-373 videótag, ezért ebben a körben képkockánként újramérés nem készült.

| Eredeti Picasa | PicasaPy-forrás (nem futásidejű mérés) | Teendő |
|---|---|---|
| A `+0x520` óta eltelt QPC-másodperc és `SlideshowEffectTime` adja a progresszió bemenetét; az alapérték 3. `SimpleSlideshow=1` alapértéknél a 1,5-szeres bemenet a `0x0072df60`-ban leírt görbéhez jut, a képpontkeverő pedig a régi `+0x444` és aktuális `+0x46c` képet keveri. | A `TimelinePanel.qml` két `Image` rétegben az előző és aktuális gyűjtemény `photos[0]` képét jeleníti meg (`34`-`37`, `46`-`80. sor). A `TimelineView.qml` a `backgroundFadeDurationMs=1400` értéket használja (`43`-`45. sor), és 0,68-ról 1-re lineárisan mozgatja a progressziót (`228`-`235`, `372`-`380. sor); a `frame_transforms` alpha-képlete ezt az időszakaszt lineáris képréteg-keveréssé alakítja (`timeline_motion.py:205-242`). | Az eredeti futás beállításait és az időbélyegzett alpha-értéket ugyanabban a Picasa-futásban kell rögzíteni. A forráskódbeli 1,400 ms önmagában nem bizonyítja az eredetivel azonos progressziót; kódváltoztatás előírása ezek nélkül nyitott. |

**Két ellenőrzési út.** A út: a `0x008001c0` közvetlen utasításolvasása a `+0x520` időbélyegtől a módágon és alpha-kvantáláson át a keverőhívásig. B út: ettől külön kódrészekből a `0x007fa7f0` konstruktor adja a `SlideshowEffectTime` alapértékét, a `0x00802230` frissítő írja a `+0x520` mezőt, a `0x009a51b0` QPC/QPF-másodpercet számol, a `0x0072df60` külön easing-függvény azonos görbealakot ad, a `0x009dc040` pedig az átadott pixelforrások közti keverést végzi. Ezek a külön kódrészek megerősítik az időalap, az alapérték, a görbe és a keverő önálló részeredményeit. A friss vak diszasszemblálás a `0x008001c0` idő-, mód- és alfaútját önállóan ugyanerre az eredményre vezette; mivel ugyanazt a függvényt olvasta, ez független ellenőrző kör, de nem külön adatút. A `SimpleSlideshow` ágak teljes összekapcsolása és a két mód viselkedésének útvonala ezért továbbra is a `0x008001c0` egyetlen utasítássorából következik; a meglévő Ghidra-dekompiláció ugyanennek a kódnak más reprezentációja, nem második független út. A futó videóhoz való kapcsolás is nyitott, mert az aktív beállításértékek és az időbélyegzett belső alpha hiányzik.

**Cáfoló kísérlet.** Azt a feltevést próbáltam megcáfolni, hogy az eltelt idő és a képréteg alpha között egyszerű lineáris kapcsolat van. A `0x008001c0` egyszerű ágában a 1,5-ös skálázás és a darabos görbe ezt cáfolja; a `0x0072df60` külön függvény utasításai ugyanazt a görbealakot támasztják alá. A cáfoló állítást külön ellenőriztem az `0x008001c0` módelágazásával: `SimpleSlideshow=1` esetén közvetlen pixelkeverés történik, míg 0 esetén transzformációs út fut; így a „mindig geometriai transzformáció is van” alternatíva is cáfolt. A videón futó konkrét beállítást ez a statikus próba nem állapítja meg.

**Bizonyítottsági fok.** A külön rutinokból ellenőrizhető részeredmények (alapérték, QPC-időalap, önálló görbealak és pixelenkénti keverés) binárissal alátámasztottak. A teljes módág és progresszió összekapcsolásának bizonyítottsági foka **feltételes**, mert az a `0x008001c0` egyetlen függvény-utasításútjára támaszkodik; a Ghidra-kimenet ugyanennek a kódnak az alternatív reprezentációja. A `job-373` videó látható 1,400/1,467 másodperces ablaka és a belső progresszió közti megfeleltetés **nyitott**: a futó példány beállításai és belső időbélyegei nincsenek meg.

**Nyitott és megszerzési út.** A tényleges futás `Preferences\SlideshowEffectTime` és `Preferences\SimpleSlideshow` értéke, valamint a `+0x520` frissítési idő és az adott képkocka `alpha` értéke NINCS MEG. A Colab/Wine futásban új videót vagy időbélyeges képsort kell készíteni, és ugyanahhoz a képkockához rögzíteni a két beállításértéket, a `+0x520` időalapot, `+0x519` állapotot, valamint a régi `+0x444` és új `+0x46c` forrást. A már létező Ghidra-kimenetek tartalmazzák a `0x008001c0` és `0x0072df60` címeket; ugyanerre a statikus kérdésre új Ghidra-kör nem szükséges. Ez nem zárja le a #6532 videó-, teljes vezérlő- és forráshalmaz-feltételeit.

**Fejlesztési átadás.** A statikus eredmény azt bizonyítja, hogy az eredeti `SimpleSlideshow=1` ága időben nemlineáris alpha-görbét használ, míg a PicasaPy-forrás lineáris, 1,400 ms-os alpha-átmenetet ír le. Az eltérő kód önmagában nem bizonyít felhasználói kimeneti hibát, mert a videó futásidejű Preferences értékei nincsenek rögzítve; ezért ebből a szakaszból önálló fejlesztői jegy még nem indokolt. A mérést követően az eredeti / nálunk / teendő táblát a mért alpha-képkockákkal kell kiegészíteni.

#### 38.2.101 A job-373 felvétel ellenőrzése és a qshow billentyűútja (#6532, 2026-11-08)

**Állapotfrissítés (2026-11-10):** e szakasz futásidejű kérdései továbbra is nyitottak; a beolvasó hívások bináris alapértékei külön lezárva a 38.2.104/105-ben.

**Kérdés és hatókör.** A #6532 kéri az eredeti Picasa Időrend videós bizonyítékát, a látható vezérlések bináris útját és a PicasaPy-val való összevetését. Ez a kiegészítés a már létező job-373 felvételt ellenőrzi újra, és a qshow billentyűkezelő útját rögzíti. Nem állítja, hogy a teljes forráslista, a minden képkockára kiterjedő animáció vagy a futó Picasa beállításai ezzel megvannak.

**Felvétel és mérés.** A helyi `~/.local/share/picasapy-meroadat/idorend/idorend-job373.mp4` fájl SHA-256 értéke `be0ba93e5ac9863f4fd98d5e3e73f03e77708a4e0cd9c7059d8d253ee13e9625`. A `ffprobe` és a dekódolt képkockák ellenőrzése:

| érték/állítás | forrás |
|---|---|
| A fájl videója H.264, 1280×1024, 15/1 fps, 1500 képkocka és 100,000 s | mérés (`ffprobe`, job-373 fájl) |
| A felvétel a Picasa könyvtárnézetét, az Időrend lapját, a Space után megjelenő OneUp/diavetítést és a későbbi könyvtárnézetet tartalmazza | mérés (job-373 dekódolt képkockák és kontaktlap) |
| A felvétel teljes kimeneti példányának SHA-256 értéke a fenti | mérés (`sha256sum`, job-373 fájl) |
| A qshow tényleges futásidejű `SlideshowEffectTime` és `SimpleSlideshow` értéke | NINCS MEG |
| A job-373 billentyű-eseménynaplója | NINCS MEG |

A videó a mérőadat-tar-on kívüli, külön helyi fájl; a tarban nem volt hozzá tartozó videótétel. A fájlt a spec-munkához nem másoltam a repóba. A videó tehát rendelkezésre áll a helyi kutatáshoz, de a release-be kerülő összehasonlító videó vagy képsor itt nem készült el.

**Bináris billentyűút.** A célfüggvény `0x00801270` a `QDrawable::vftable` 12. slotja (vtable `0x00cbd66c`, slot byte offset `+0x30`; RTTI-index). A függvény utasításai a `WM_KEYDOWN` (`0x100`) üzenettípust dolgozzák fel; `WM_CHAR` (`0x102`) és az üzenetazonosító 0 külön ága nem kezeli billentyűként.

| gomb | bináris út és pontos érték | megfigyelés/korlát |
|---|---|---|
| Escape | `0x00801270` → `0x007fb820` | qshow kilépési út; a pontos utána kijelölt kép a videó eseménynaplója nélkül nem rendelhető ehhez a gombhoz |
| Left, Up | `0x00801270` → `0x008011b0`; a hívó a `0x00cf3a48` f32 konstansból 2,0-t ad át `0x007fd0c0`-nak | `0x007fd0c0` a qshow `+0x2f8` pályaadatát és QPC-időt használja, majd a `0x0072df60` görbét hívja; ez a pozitív irányú út |
| Right, Down | `0x00801270` → `0x00801210`; ugyanennek a 2,0 értéknek az előjele negálódik a `0x007fd0c0` hívása előtt | ez a negatív irányú út |
| Space | a `+0x3bb` állapotjelző szerint a `0x00801130` vagy a `0x00803110` ág | a videó a OneUp/diavetítés állapotát mutatja, de nem tartalmaz eseménynaplót; a két ág pontos futásidejű választása NINCS MEG |
| Ctrl+Space | külön, `+0x3ba` jelzőt vizsgáló ág | ennek teljes látható hatása ebben a körben NINCS MEG |

Az `0x00cf3a48` cím nyers PE-adatként kiolvasott f32 értéke 2,0; a `0x007fd0c0` az aktuális qshow-pályaadatot olvassa, QPC-alapú időpontot számol, a hívó paraméterét hozzáadja a QPC-időhöz, majd a görbeértéket frissíti. Ez a bináris út a gombokhoz tartozó irányt és átadott időparamétert igazolja; önmagában nem bizonyítja, hogy a job-373 konkrét futásban minden gombot lenyomtak.

**Videós cáfoló kör és az időtartam helyesbítése.** A 38.2.85-ben idézett `n=226→247` (21 képkocka, 1,400 s), illetve `n=344→366` (22 képkocka, 1,467 s) párok látható állapotok közti választott mintavételi ablakok. A teljes képkockasor újraellenőrzése nem azonosította a két átmenet első és utolsó mozgó képkockáját; néhány szomszédos képkocka kis pixelkülönbsége a tömörítésből is eredhet. Ezért a két érték **nem** a teljes animáció igazolt időtartama. A teljes látható átmenet kezdő- és végképkockája: NINCS MEG. Beszerzési út: ugyanazon új Picasa-futás teljes képkockasorának veszteségmentes vagy képenkénti mentése, az események pontos időbélyegével.

**PicasaPy-összevetés.**

| Eredeti Picasa | Jelenlegi PicasaPy | Teendő |
|---|---|---|
| Az eredeti qshow a `0x00801270` handlerben kezeli az Escape, Left/Up, Right/Down és Space ágakat; a nyílirányú hívó a bináris `0x00cf3a48` 2,0 értékét adja a `0x007fd0c0` pályafrissítőnek. | A `TimelineView.qml:393-406` az Escape, balra/jobbra és Space gombot kezeli; a `TimelineView.qml:106-115` a nyilakhoz irányított `step` hívást és 2000 ms-os mozgásbeállítást ír le. Ez a fájlforrásból leolvasott implementáció, nem PicasaPy futásidejű videómérés. | A billentyűk és a léptetés statikus kódútjai megvannak. A két mozgás képkockánkénti egyezése és a konkrét futásidejű bemenetek NINCS MEG; ezeket összehasonlítható, időbélyeges eredeti és PicasaPy felvétellel kell mérni. |
| A job-373 videón látszik a könyvtár → Időrend → OneUp → könyvtár nézetsor; a kártyákon és nagy háttérképen lévő felirat/csíkozás a forrásképek része (38.2.93). | A PicasaPy jelenlegi kártya- és háttérforrását a `timeline_controller.py:195-283` és `TimelinePanel.qml:34-80` írja le; a fájlszintű felirat/csíkozás-eredet nem futásidejű bizonyíték. | A job-373 felvétel és a korábbi képelemzés alátámasztja a tartalmat, de a teljes kártyasorrend, token futásidejű rekordjai és a release-összehasonlító képsor NINCS MEG. A forráslista teljes visszafejtéséhez külön mérés kell. |

**A két független út és bizonyítottsági fok.** A út: a `0x00801270` utasításainak célzott diszasszemblálása, a gombágaktól az `0x008011b0`/`0x00801210` hívókon át a `0x007fd0c0` pályafrissítőig; a `0x00cf3a48` f32 adatértéket a PE-ből külön olvastam ki. B út: az RTTI/vtábla-index a `0x00801270`-et a `QDrawable` eseménykezelő slothoz rendeli, és ettől függetlenül a job-373 dekódolt képkockái igazolják, hogy a rögzített futásban megjelentek az Időrend és OneUp felületek. Az utak egyeznek a kezelő azonosításában és a megfigyelt felületek létezésében; a videó nem naplózza a gombokat, tehát a gomb→képkocka okozati megfeleltetés **feltételes**. A nyílágak statikus cím/előjel-értelmezése binárisból ellenőrzött, de a konkrét job-373 eseménysor nyitott. A videófájl megléte/tartalma **megerősített** két egymástól független mérési ellenőrzéssel: fájlmetaadat/hash, illetve dekódolt képkockák.

**Cáfoló kísérlet.** Azt a következtetést próbáltam cáfolni, hogy a 38.2.85 két időértéke a teljes animációtartam. A szomszédos képkockák pixelkülönbségét ugyanazzal a ROI-val végignézve a kiválasztott határok nem adták meg az első és az utolsó animációs képkockát; a kis különbségek tömörítési maradvánnyal is magyarázhatók, ezért nem tekintettem őket mozgásnak. A cáfoló eredményt ellenőriztem a frame-rate és képkockaszám alapján: a két különbség valóban a kiválasztott indexek közötti idő, de ez nem teszi őket a teljes átmenet időtartamává. A 2,0 érték ellenpróbájaként a nyers `0x00cf3a48` bájtokat olvastam ki, és a callerben a `0x007fd0c0` felé vezető mindkét nyilas ágat ellenőriztem; a konstans és az irány előjele egyezik a hívó utasításával.

**Nyitott.**

- A job-373 futás `Preferences\SlideshowEffectTime`, `Preferences\SimpleSlideshow` tényleges értéke, a `+0x520` frissítési idő és a képkockánkénti alpha: NINCS MEG. Megszerzés: új Colab/Wine futásban a beállításértékek és qshow mezők időbélyeges rögzítése a videóval együtt.
- A qshow `+0x50c` token aktuális értéke, a posting-list teljes rekord-/képazonosító-sorrendje és az összes látható kártya forráslistája: NINCS MEG. Megszerzés: futásidejű token és `CSlice+0x64` lista rögzítése, majd azonosítók képkockákkal való összevetése; a bináris statikus út a 38.2.63-ban dokumentált.
- Az átmenetek első és utolsó látható képkockája, valamint a bal/jobb/Space/Escape események konkrét képkockái: NINCS MEG. Megszerzés: időbélyeges eseménynapló és képkockasor ugyanabból a futásból.
- A release-be kerülő Picasa/PicasaPy összehasonlító videó vagy képsor: NINCS MEG; a helyi job-373 videó a kutatási könyvtárban van, nem került be a repóba.
- A `0x00801270`, `0x007fd0c0` és `0x008001c0` címek meglévő Ghidra-kimenetben is szerepelnek; ezekhez az itt vizsgált statikus kérdésekhez új Ghidra-kört nem kérek.

**A #6532 „Kész, ha” állapot.** A helyi eredeti Picasa-felvétel elérhető és az Időrend/OneUp felületek dekódolt képkockákon látszanak. A qshow billentyűút egy részére van bináris cím, de a teljes vezérlőlista, animáció, futásidejű forráshalmaz és Preferences-állapot még nem zárt. A teljes spec minden megvalósítandó pontja ezért nem tekinthető címekkel igazoltnak, és maradtak „NINCS MEG” pontok. Release-összehasonlító képsor/videó és implementációs jegy megnyitása a hívó feladata; a kutatás alapján ebből a szűk billentyűútból önálló kódváltoztatás nem következik.

#### 38.2.102 Az Időrend teljes kártyapálya-, mélységi alfa-, köteg- és felirat-leltára (#6532, 2026-11-08)

**Állapot:** a szakasz saját összevető táblája a 2026-11-08-i PicasaPy-kódállapotot tükrözte; a #6713 utáni állapotot és a még nyitott kérdéseket a 38.2.105 rögzíti.

**Kérdés és hatókör.** A #6532 2. pontja előírja a bináris feltárást mindenre, ami az Időrend bemutatóján látszik: a kártyák 3D-s pályája és koordinátatranszformációja, a Z-mélység szerinti láthatósági szűrő és a mélységi átlátszósági (alfa) képlet, a kötegen belüli kártyák véletlen szórása, a bélyegkép LOD-választása, a vezetőpontok és a feliratok elhelyezése, valamint a dátumskála végfeliratainak forrása. Ez a szakasz ezeket a részeket tisztázza zárt képletekkel és bináris címekkel.

**Forrás és módszer.** A helyi `Picasa3.exe` célzott utasításszintű diszasszemblálása (`annot_disasm.py`, capstone) a `0x007fc010`, `0x007fd180`, `0x008014d0`, `0x007fa5b0`, `0x00803b50`, `0x00a6ac90`, `0x007fee70` függvényekre; független ellenőrzésként a meglévő Ghidra-dekompilációk (`2026-10-21-idorend-7.txt`, `2026-11-05-idorend-6532-kartyakeszlet.txt`, `2026-11-05-idorend-6532-retegek.txt`); a konstansok nyers kiolvasása a PE `.rdata` szekciójából (`pefile`).

**1. Kártyák 3D pályája és transzformációja a lapon (`0x007fc010`).**

- **Bemenet és görbepont:** A kártyasáv (`obj = this + 0x2f8`) minden `i`-edik rekordjára a paraméter `t_i = i · S + O`, ahol `S = 0.04999999888241291` (f64 `0x00cf4e30`), `O` az aktuális görgetési eltolás (`0x007fc010:336`). A `0x007fbab0` köbös racionális Bézier függvény a `runtime/bezier.txt` négy vezérlőpontjából kiszámítja a 3D `(X, Y, Z)` lebegőpontos koordinátákat (`0x007fc010:362-365`; 38.2.61).
- **Láthatósági szűrő:** A kód ellenőrzi: `Z > 0.1` (f64 `0x00c7dd30`). Ha `Z ≤ 0.1`, a kártya a látható kártyák tömbjébe (`[obj+0x80]`) nem kerül be (`0x007fc010:366`, `0x007fc100`-`0x007fc128`).
- **3x3 transzformációs mátrix:** A kártya `(W_card, H_card)` méretéből (`[record+0x98]`, `[record+0x9c]`) és a lap `(W_lap, H_lap)` téglalapjából (`param_2: [left, top, right, bottom]`, ahol `W_lap = right - left`, `H_lap = bottom - top`) három egymást követő mátrixművelettel (`0x009e6340`) épül fel:
  1. *Középre igazítás:* `T1 = translate(-W_card / 2, -H_card / 2)` (`0x007fc2dc`-`0x007fc2f4`).
  2. *Skálázás Z mélységgel:* `S_z = scale(Z · scale_factor, Z · scale_factor)`, ahol a szorzó `[obj+0x28] = 1.0` (`0x007fc32a`-`0x007fc35c`).
  3. *Képernyőre helyezés:* `T2 = translate(W_lap · X, H_lap · Y)` (`0x007fc371`-`0x007fc3c3`).
  A kártya középpontja a lapon tehát `(W_lap · X, H_lap · Y)`, mérete `(W_card · Z, H_card · Z)`.

**2. Mélységi átlátszósági (alfa) képlet (`0x007fc010:483-490`, `0x007fc3c8`-`0x007fc439`).**

A kártya mélységi alfája a távolodással nemlineárisan csökken:
- `u = max(0.0, (1.0 / Z - 1.0) / 9.0)` (f64 `0x00cf3ef8 = 9.0`).
- `fade = pow(u, 1.5)` (f32 `0x00cf3ec4 = 1.5`, `0x005568e0` CRT `pow`).
- `alfa_depth = round((1.0 - fade) · 256.0)` (f64 `0x00cf39d8 = 256.0`).
- Az érték a rekordba kerül: `record[+0xa0] = alfa_depth`.
- *Kapcsolat a láthatósági szűrővel:* Ha `Z = 1.0`, `u = 0.0` → `fade = 0.0` → `alfa_depth = 256` (100% fedés). Ha `Z = 0.1`, `(1.0/0.1 - 1.0) / 9.0 = 9.0 / 9.0 = 1.0` → `fade = pow(1.0, 1.5) = 1.0` → `alfa_depth = 0` (0% fedés). A `Z ≤ 0.1` láthatósági küszöb pontosan az a pont, ahol az alfa eléri a 0-t.
- *Nyitó beúsztatás:* A rajzoláskor (`0x007fd180:709`) az átlátszóság: `alfa_final = (record[+0xa0] · p) >> 8`, ahol `p = round(clamp(t_sec, 0.0, 1.0) · 256.0)` az első másodpercben (`0x00800a30`).

**3. Kötegen belüli kártyák véletlen szórása és LOD-választása (`0x008014d0`, `0x00a6ac90`).**

**HELYESBÍTVE a 38.2.150-ben: a `0x008014d0` kapuzott (`Ctrl+F`/`Ctrl+B` nélkül `_rand`-hívás nélkül kilép), és mezői helyzet és sebesség, nem kártyaeltolás; az alábbi "köteg szórása" olvasat megdőlt. A LOD-választás (`0x00a6ac90`) állítása érintetlen.**

- **Véletlen eltolás a kötegben (`0x008014d0:83-95`, `0x008015ad`-`0x008016c6`):**
  A gyűjtemény képeit bejárva a kód a CRT `_rand()` (`0x00c08221`) hívásaiból IEEE-754 bitmanipulációval `[0.0, 1.0)` lebegőpontos számokat állít elő, kivon `0.5`-öt (`0x00c72150`), majd megszorozza a `0x00cf3fd0` qword konstanssal (`0.15000000596046448`):
  - `dx = (rand_x - 0.5) · 0.15` → tartomány `[-0.075, +0.075]`.
  - `dy = (rand_y - 0.5) · 0.15` (ha `+0x3bc` aktív, `+0.5` előjeles korrekcióval).
  - Ezek a `record[+0xd4]` és `record[+0xd8]` mezőkbe kerülnek (`0x008016b8`, `0x008016c6`), és a köteg kártyáinak szórását adják.
- **Bélyegkép LOD-választás (`0x00a6ac90`):**
  A kártyarajzoló (`0x007fd180`) a `0x00a6ac90(image, matrix, 1.2f)` hívással választja ki a bélyegképszintet (f32 `0x00c7dd44 = 1.2`). A függvény a 2D mátrix bázisvektorainak hosszából skálát számol: `scale = max(sqrt(m00² + m01²), sqrt(m10² + m11²)) · 1.2`, majd az exponensből `lod = clamp(floor(log2(scale)), 0, max_lod - 1)` szintet választ.

**4. Jobb felső feliratok, 10 vezetőpont és a dátumskála végfeliratai (`0x007fee70`).**

- **Gyűjtemény neve:** `y = 130.0` (f32 `0x00cf4e8c`), jobbra zárt `x = W_lap - 90 - width_text` (`[this+0x2d0] - 0x5a - width`), `HelveticaNeue MediumCond`, `0x190`, `0x1c`, méret `0.7142857` (`0x00cf4144`), fekete árnyék `(x+1, y+1)`-en `floor(p · 127 / 256)` alfával, világos szöveg `(x, y)`-on `floor(p · 255 / 256)` alfával.
- **Hónap és év:** `y = 158.0` (f32 `0x00cf4e88`), jobbra zárt `x = W_lap - 90 - width_text`, `HelveticaNeue Condensed`, `0x190`, `0x14`, formátum `ytDateTime::Format2` `%s %d`, ugyanazzal a szín- és árnyék-képlettel.
- **10 vezetőpont köbös Bézier íve (`0x007fee70:1234`):**
  - Kezdőpont: `P0 = (A - 16, B)`, ahol `A, B` a jobb felső név és dátum befoglaló téglalapjának jobb és alsó széle.
  - Végpont: `P3 = ((r[+0xdc] + r[+0xe4]) · 0.5, r[+0xe0] - 20)`, vagyis a fókuszban lévő kártya felső élének felezőpontja mínusz 20 px.
  - Kontrollpontok: `P1 = (P0.x, P0.y + 50.0)`, `P2 = (P3.x, P3.y - 50.0)` (f64 `0x00cf3bd8 = 50.0`).
  - Simítás: `(előző + új) · 0.5` (`0x00c72150`), pontok paramétere `t = i / 9.0` (f64 `0x00cf3ef8 = 9.0`, `i = 0..9`), átlátszóság `p`.
- **Dátumskála végfeliratai (`0x007ff5da`-`0x007ff761`):**
  A közvetlen utasításolvasat szerint a dátumvonal két végén a qshow rekordtömb **0. és N-1. rekordjának** hónap-éve áll. Ezt a lekérdező-útvonalra nézve a 38.2.103 megerősítette: a `CThumbDB+0x48` másodlagos vtable `+0x20` slotja `0x0044f7c0`. A rekordok növekvő dátumkulcs szerinti rendezése lezárva (38.2.105); a lista teljes katalógushoz való viszonya és a PicasaPy adathalmazával való azonossága továbbra is nyitott. A videón `May 2009` és `November 2026` látható. Bal felirat: jobbra zárva `track_left - 8`, `y = track_bottom - 3`; jobb felirat: balra zárva `track_right + 8`, `y = track_bottom - 3`. Szín: fekete, alfa `floor(floor(p · 127 / 256) · p / 256)`. Azt, hogy ezek a teljes könyvtár időhatárai-e, a videó önmagában nem dönti el.

**5. Sebességcsillapítás és megállási fókuszválasztás (`0x007fc010`, `0x007fd8c0`).**

- A sebesség csillapítása: `V = V · 0.95` (f64 `0x00cf40b0`) lépésenként (`0x007fc010:352`).
- A sáv megállt, ha `|V| ≤ S · 0.01 = 0.04999999888241291 · 0.01 = 0.0004999999888241291` (f64 `S@0x00cf4e30`, `0x00cf40b8 = 0.01`) és nincs futó animációs szakasz (`0x007fd8c0:1298`).
- Megálláskor a fókuszgyűjtemény az a rekord, amelynek `X` koordinátája legközelebb esik a `0.666`-hoz (f64 `0x00cf4860`); ennek indexe kerül a `[this+0x510]`-be, és ez indítja a `0x008018a0` gyűjteményváltást, jobb felső feliratcserét és háttér-átúsztatást.

**Összevetés a PicasaPy-jal.**

| Eredeti Picasa (binárisból igazolt) | Jelenlegi PicasaPy | Teendő |
|---|---|---|
| A kártya Z-mélységének alfája: `u = max(0, (1/Z - 1)/9)`, `fade = pow(u, 1.5)`, `alfa = round((1 - fade) · 256)` (`0x007fc010`, `0x005568e0`). | A `timeline_motion.py:90-97` ezt számolja; a `TimelinePanel.qml:208` a kártyaréteg alfájára alkalmazza. | A képlet és a QML-kötés egyezik; további fejlesztés nem igazolt. |
| Láthatósági szűrő: `Z > 0.1` (`0x007fc010:366`, `0x00c7dd30`). | A `timeline_motion.py:28, 122` `VISIBLE_WIDTH = 0.1` küszöböt használ. | Megegyezik. |
| Kötegen belüli kártyánként két CRT `_rand()` hívásból képzett szórás: `dx,dy ∈ [-0.075,+0.075]` (`0x008014d0`, `0x00cf3fd0`). | A `timeline_motion.py:100-131` ugyanebbe a tartományba eső eltolást ad, indexekből magozott xorshift PRNG-vel; `TimelinePanel.qml:250-258` ezt alkalmazza. | A képi szórás tartománya megfelel. A PRNG-algoritmus eltér; az eredeti futás seedje és a konkrét kártyaeltolások NINCS MEG. Ezért a forráskülönbségből önmagában nem igazolt felhasználói eltérés. |
| Jobb felső feliratok: név `y = 130`, hónap-év `y = 158`, jobbra zárt `x = W - 90 - width`, 1 px fekete árnyék `(x+1, y+1)` (`0x007fee70`). | A `TimelinePanel.qml:335-398` ugyanezeket a baseline-helyeket, jobbra zárást és +1 px fekete árnyékot használja. | A forrásmodell megegyezik; további fejlesztés nem igazolt. |
| 10 ponton mintavételezett köbös Bézier ív: `P1 = P0 + (0,50)`, `P2 = P3 - (0,50)`, `P3 = (kártya_közép, kártya_fent - 20)` (`0x007fee70`). | A `timeline_motion.py:134-162` képlete egyezik; a `TimelinePanel.qml:137-148` a feliratblokk és az első kártya koordinátáiból adja a végpontokat, a dátum alapvonala alatti eltolt kezdőpontot a job-373 mérése rögzíti. | A képletet a #6713 átvezette; az illeszkedő kezdőpont eltolását mérés támasztja alá (38.2.102). További fejlesztés nem igazolt. |
| A dátumskála két széle a qshow `0xf8` bájtos rekordtömbjének első és utolsó rekordjához fordul: a tömb címe `[this+0x3a8]`, a rekordszám `[this+0x3ac] >> 1`; a dátumlekérés a `CThumbDB+0x48` vtable `+0x20` slotján történik (`0x007ff476`-`0x007ff496`, `0x007ff4b8`-`0x007ff4f3`). A qshow kártyalista a 64 bites dátumkulcsok szerint növekvően rendeződik (lezárva: 38.2.105); a fókuszválasztó külön kiválasztja a `0x00cf4860`-hoz legközelebbi X koordinátájú rekordot, majd annak első dwordját adja vissza (`0x007fd8c0`-`0x007fd97a`). | A `timeline_controller.py:183-264` a nem rejtett fotókból mappákat és a nem üres, indexelt albumokból albumkártyákat állít elő; a `timeline_controller.py:223-231,321-335` a globális dátumhatárokat és a gyűjtemények legkorábbi tagdátumát számolja. | A qshow CAlbumState-descriptorainak teljes forráshalmaza, a dátumkulcs pontos jelentése és a PicasaPy-gyűjteményekkel való futásidejű azonossága nincs megmérve. A korábbi „fókuszgyűjtemény első/utolsó fotója” eltérésállítás téves volt; a dátumhatár-javításról a halmazok azonosítása előtt nem következik döntés. |
| Sebességcsillapítás: `V = V · 0.95`, megállási küszöb `|V| ≤ 0.04999999888241291 · 0.01 = 0.0004999999888241291`, a legközelebbi `X = 0.666` célú kártya kap fókuszt (`0x007fc010`, `0x007fd8c0`, `0x00cf40b0`, `0x00cf40b8`, `0x00cf4860`). | A `TimelineView.qml:143,367-371` hívásonként `0.95`-tel csökkenti a sebességet és a `CARD_STEP · 0.01` küszöbnél állítja meg; a `timeline_motion.py:26-28,141-159` ugyanezt a lépésközt, küszöböt és `FOCUS_X = 0.666` célt használja, a `finishCarouselMotion()` ezt a fókuszindexet választja (`TimelineView.qml:212-230`). | A forrásszintű csillapítási szorzó, küszöb és fókuszcél megfelel az eredetinek. Az eredeti és a PicasaPy frissítési ütemének, illetve a tényleges megállási képkockának az összehasonlítása még hiányzik; ebből most nem következik kódmódosítás. |

**Bizonyítottsági fok.** A kártyapályára, a Z-szűrőre és az átlátszóságra vonatkozó állítások, valamint a köteg-szórás és LOD a felsorolt bináris és Ghidra-források alapján megerősítettek. A feliratok elhelyezése és a vezetőpont-görbe képlete a közvetlen utasításolvasattal alátámasztott; a végfeliratok első/utolsó rekorddátumot kérő mechanizmusa a 38.2.103 független vtable-útjával megerősített. A lista dátumkulcs szerinti növekvő rendezése megerősített a 38.2.105-ben; a CAlbumState teljes forráshalmaza, a kulcs pontos naptári jelentése és a PicasaPy gyűjteménylistájával való azonosság nyitott.
1. A kártyák transzformációja, Z-mélysége, 0.1-es szűrője és az alfa-képlet az utasításszintű olvasatból (`0x007fc010`), a PE-konstansokból és a meglévő Ghidra-dekompilációból (`2026-10-21-idorend-7.txt`) egyezően igazolt.
2. A kötegen belüli szórás és LOD-választás a `0x008014d0` és `0x00a6ac90` utasításaiból és a `2026-11-05-idorend-6532-kartyakeszlet.txt` dekompilációjából megerősített.
3. A jobb felső feliratok koordinátái és a 10 vezetőpont Bézier-képlete a `0x007fee70` utasításaiból és a `2026-11-05-idorend-6532-retegek.txt` dekompilációjából megerősítettek. A dátumskála végfeliratainak rekordforrása ugyanebből a függvényből közvetlenül kiolvasható, de független ellenőrző kör hiányában feltételes; a „teljes könyvtár” jelentésű következtetés és a PicasaPy-val való egyezés külön mérésre vár.

**Cáfoló kísérletek.**
- *Cáfoló 1 (mélységi alfa):* Megpróbáltam cáfolni a `pow(u, 1.5)` képletet egy egyszerűbb lineáris vagy exponenciális fade feltevésével. A `0x007fc40f` címen levő hívás a `0x005568e0` függvénybe ugrik, amely a CRT `pow` függvényét (`0x00c0b410`) hívja `0x00cf3ec4` = 1.5 kitevővel. A `Z=0.1` küszöb vizsgálata (`0x007fc100`) pontosan megegyezik a `(1/Z - 1)/9 = 1.0` gyökhellyel, így az alfa-képlet zárt és koherens.
- *Cáfoló 2 (PicasaPy dátumcímkéinek hatóköre):* Azt próbáltam ellenőrizni, hogy a `TimelinePanel.qml` mezőinek aktuális gyűjteményobjektumból olvasása azt jelenti-e, hogy a PicasaPy az adott gyűjtemény első és utolsó fotójának dátumát mutatja. A `timeline_controller.py:201-209,273-274` ezt cáfolja: a két mezőt egyszer, a teljes `records` halmazon számított minimum/maximum EXIF-dátumból készíti, majd minden gyűjteményhez ugyanazt rendeli; a QML valóban az aktuális objektumról olvassa e mezőket. A cáfolat tehát a PicasaPy-forrásra érvényes, de nem dönti el, hogy ezek az értékek megegyeznek-e az eredeti qshow első/utolsó rekordjának dátumával. A bináris oldalra kért friss, vak ellenőrző a `capstone` hiánya miatt nem tudta kiolvasni `0x007fee70` utasításait; a videó végfeliratokat mutat, de nem rögzíti a mögöttes rekordokat. A végpontok tényleges összehasonlítása nyitott.

**A #6532 „Kész, ha” állapot.**
1. ✅ Az eredeti Picasa Időrendjéről van helyben elérhető, dekódolható videó (`job-373`, 100 s, 1500 képkocka); a rögzítő Colab-futás és a futó bináris hash-e ebből a videóból nem igazolható.
2. ⛔ A specifikáció nem zárja le az összes megvalósítandó pontot: a 38.2.101-ben felsorolt Preferences-értékek, a teljes futásidejű qshow-forráslista, az eseménynaplóhoz rendelt képkockák és az összehasonlító kiadási képsor/videó továbbra is „NINCS MEG”.
3. ⛔ A PicasaPy-forrás és az eredeti bináris több eleme össze lett vetve, de a végfeliratok qshow-rekordjai és a PicasaPy globális dátumhatárai közötti tényleges egyezés/eltérés nincs mérve; ezért a korábbi konkrét végfelirat-javítás nem adható át fejlesztési követelményként.
4. ⛔ A megvalósítási jegy megnyitása és állapotának ellenőrzése a hívó feladata; a GitHub-állapot ebben a kutatási körben nem ellenőrizhető.
#### 38.2.103 A dátumskála végfeliratai a fókuszgyűjtemény váltásakor változatlanok (#6532, 2026-11-08)

**Kérdés.** A 38.2.102 nyitva hagyta, hogy a dátumvonal `May 2009` és `November 2026` felirata a kiválasztott gyűjtemény szélső dátumát, vagy a qshow saját rekordlistájának széleit mutatja-e.

**Forrás és módszer.** A helyi `Picasa3.exe` `0x007fee70` függvényének célzott, utasításszintű diszasszemblálása (`annot_disasm.py`, a bináris index szerinti 3600 bájt); összevetés a már meglévő `2026-11-05-idorend-6532-retegek.txt` Ghidra-kimenettel; a `job-373` MP4 teljes dekódolása után kiválasztott `n=150`, `n=300` és `n=420` képkocka vizuális összehasonlítása. Az átmeneti PNG-k a munkafa `.bt/` könyvtárába kerültek.

**Bináris út (feltételes a rekordlista teljes hatókörére).** A `0x007ff476` a `[this+0x3a8]` rekordlista első rekordjának azonosítóját olvassa. A `0x007ff493`-nál a `[this+0x2f4]+0xc4+0x48` objektum virtuális táblájának `+0x20` slotja kapja az azonosítót; a hívás a `0x007ff496` címen történik. A dátumot a `0x0098c780` `%s %d` hónap-év formázó alakítja felirattá (`0x007ff4a9`). A jobb végpontnál a függvény a `[this+0x3ac]` mezőt felezi (`0x007ff4c6`), `0xf8` bájtos rekordmérettel kiszámítja az utolsó rekord címét (`0x007ff4c8`-`0x007ff4ce`), majd ugyanennek a virtuális `+0x20` lekérdezőnek adja át (`0x007ff4f0`-`0x007ff4f3`) és a `0x0098c780`-nal formázza (`0x007ff506`). A meglévő Ghidra-kiírás ugyanebben a függvényben ugyanezt a mező- és hívásszerkezetet tartalmazza; ez a gépi kód alternatív reprezentációja, önmagában nem második futásidejű adatút.

**A rekorddátum-lekérdező azonosítása: helyesbítés (2026-11-09; megerősített).** A korábbi változat tévesen a `CThumbDB` elsődleges vtable-jének `+0x20` slotját (`0x00423300`) nevezte meg. A `0x007fee70` hívó utasításai valójában a `[this+0x2f4]+0xc4` objektum `+0x48` másodlagos alobjektumának vtable-jét olvassák, majd annak `+0x20` slotját hívják (`0x007ff47c`-`0x007ff496`, `0x007ff4d9`-`0x007ff4f3`). A `0x00415790` konstruktor a fő vtable-t `0x00c81f78`-ra (`0x004157fd`), a `+0x48` alobjektum vtable-jét `0x00c81fa4`-re (`0x00415804`) állítja. A bináris PE-tábla `0x00c81fc4` címen levő, azaz a másodlagos vtable `+0x20` slotja `0x0044f7c0`; ezzel szemben a fő tábla `0x00c81f98` slotja `0x00423300`, másik függvény.

A `0x0044f7c0` célfüggvény diszasszemblálása sorszámot ellenőriz a tárolt elemszámmal, majd a sorszámhoz tartozó 64 bites értéket olvassa a tömbből; határon kívül a külön 64 bites tartalékértéket adja (`0x0044f857`-`0x0044f884`). Nem keres minimumot vagy maximumot. A `0x007fee70` az első (`[this+0x3a8]`) és a darabszámból számolt utolsó (`0x007ff4c6`-`0x007ff4ce`) rekordazonosítót adja e lekérdezőnek, a visszakapott 64 bites értéket pedig a `0x0098c780` formatterhez küldi (`0x007ff4a9`, `0x007ff506`). A formatterhez tartozó PE-szövegek a `%s %d` mintát (`0x00c87dd0`) és a `ytDateTime::Format2` nevet (`0x00cd89c4`) adják. Ezért a bináris mechanizmus az első és az utolsó qshow-rekord dátumértékének formázása; a lista időrendi rendezése és teljessége ebből nem következik.

**Videómérés.**

| Videóképkocka | Fókuszban látható gyűjtemény | A dátumvonal bal és jobb végfelirata |
|---:|---|---|
| `n=150` (10,000 s) | `2009_majus` / `May 2009` | `May 2009` / `November 2026` |
| `n=300` (20,000 s) | `2014_november` / `November 2014` | `May 2009` / `November 2026` |
| `n=420` (28,000 s) | `2019_marcius` / `March 2019` | `May 2009` / `November 2026` |

A három vizsgált képkockán a dátumvonal feliratai változatlanok, miközben a jobb felső fókuszfelirat három különböző gyűjteményt mutat. Ez a mérés azt támasztja alá, hogy a dátumvonal nem a látható fókuszgyűjteményhez tartozó dátumpárt jeleníti meg. Nem bizonyítja önmagában, hogy a `[this+0x3a8]` rekordlista a teljes Picasa-katalógus valamennyi képét tartalmazza.

**Eredeti / nálunk / teendő.**

| Eredeti Picasa | Jelenlegi PicasaPy (forráskód, nem futásidejű mérés) | Teendő |
|---|---|---|
| A qshow dátumvonalának két felirata a saját `+0x3a8` rekordlistájának első és utolsó rekordazonosítójához tartozó dátumból készül (`0x007fee70`, `0x007ff476`-`0x007ff506`; lekérdező: a `CThumbDB+0x48` másodlagos vtable `+0x20` slotja, `0x00c81fc4` → `0x0044f7c0`). A `0x00423300` a fő vtable másik, rekordkereső slotja. A job-373 három vizsgált csoportja alatt a feliratok azonosak. | A `timeline_controller.py:223-231` a `_collections_to_qml` hívásnak átadott `records` dátumai közül egyszer számít minimumot és maximumot, majd ezeket minden gyűjtemény rekordjához rendeli (`:295-296`). A `TimelinePanel.qml:574-577,666-669` az aktuális gyűjtemény objektumáról olvassa ki a két címkét. | A két megjelenítési mód gyűjteményváltás közbeni viselkedése egyezik, de a PicasaPy `records` készletének és a Picasa qshow `+0x3a8` rekordlistájának tényleges azonossága nincs mérve. A qshow lista dátumkulcs szerinti növekvő rendezése lezárva (38.2.105); a kulcs naptári jelentése és a címkék „legkorábbi/legkésőbbi” értelmezése a teljes forráshalmaz ismerete nélkül nem állítható. A rekordlisták futásidejű azonosítása előtt e részből nem következik dátumhatár-javítás. |

**A két út és bizonyítottsági fok.** A út: a `0x007fee70` utasításai azonosítják a `[this+0x2f4]+0xc4+0x48` másodlagos vtable `+0x20` híváshelyet, és megmutatják az első/utolsó rekordazonosítót, valamint a 64 bites kimenet formatterhez továbbítását. B út: külön konstruktorolvasat a `+0x48` alobjektumot a `0x00c81fa4` táblához rendeli (`0x00415790`, `0x00415804`); a nyers PE-vtable `0x00c81fc4` slotja `0x0044f7c0`, amelynek külön diszasszemblálása sorszám szerinti 64 bites értéket ad vissza. A két út egyezik a lekérdező céljában és a rekordérték szerepében. A téves fő-vtable-jelölt `0x00423300`-at a nyers tábla `0x00c81f98` slotja adja, nem a qshow által használt másodlagos slot. A végpontértékek formázásának mechanizmusa **megerősített**. A qshow lista növekvő dátumkulcs-sorrendje a 38.2.105-ben külön builder/rendező útból megerősített; a lista teljessége, a kulcs naptári jelentése és a PicasaPy `records` készletével való azonossága továbbra is **nyitott**. A job-373 képkockamérése korábban, a 38.2.103-ban rögzített vizuális ellenőrzés; a Ghidra-kiírás nem külön út, mert ugyanazon hívó másik reprezentációja.

**Cáfoló kísérlet.** Azt a jelöltet próbáltam cáfolni, hogy a feliratkód a `CThumbDB` fő vtable `+0x20` slotját (`0x00423300`) használja dátumlekérdezőként. A hívó utasítás a `+0x48` alobjektum vtable-pointerét tölti be; a konstruktor a másodlagos vtable mezőbe `0x00c81fa4`-et ír; a nyers PE-ben ennek `+0x20` slotja (`0x00c81fc4`) `0x0044f7c0`, míg `0x00423300` a fő vtable `0x00c81f98` slotjában található. Az eredeti azonosítás tehát **megcáfolódott**. A `0x0044f7c0` lekérdező és a hívó két külön statikus olvasata igazolja a lekérdezett dátum-qword útját; a kártyaépítő és a rendező összevetése a 38.2.105-ben igazolja a növekvő dátumkulcs-sorrendet. A CAlbumState bemeneti lista teljes tartalmát, a szűrők szemantikáját és a PicasaPy-adatkészlettel való azonosságot ezek a próbák nem döntik el; ezek **NINCS MEG** állapotban maradnak. A korábbi job-373 videómérés fókuszváltás alatti változatlan végfeliratai csak a fókuszgyűjteménytől való függetlenséget támasztják alá.

**Nyitott.** A qshow `[this+0x3a8]` rekordlistájának pontos tagsága, teljessége, a két builder-szűrő szemantikája és a PicasaPy gyűjteménylistájával való azonossága **NINCS MEG**. Megszerzéséhez egy azonos Picasa-futásban rögzíteni kell a CAlbumState descriptor-azonosítóit, a qshow rekordlista tagjait, a fókuszgyűjteményt és a két végfelirat dátumkulcsát, majd ezeket a PicasaPy azonos mappakészletből előállított gyűjteménykártyákkal összevetni. A kártyalisták qword dátumkulcs szerinti rendezése binárisból már lezárva (38.2.105). A helyi böngészőben nem volt Colab-fül; a helyi Colab-indító GitHub API-t igényel, ezért új futást ebben a körben nem indítottam.

**Adatíró-jelölt cáfoló ellenőrzése (2026-11-09).** A `0x00415790` konstruktor a `0x00c81fa4` másodlagos vtable-t a `+0x48`, a `0x00c820d0` vtable-t a `+0x50` mezőbe állítja. A `0x00c820e0` slot nyers PE-adat szerint a `0x0049f310` thunkra mutat; a thunk `sub ecx,8; jmp 0x0044fa80`, vagyis a hívott függvény `this` mutatóját a `+0x48` alobjektumra igazítja. A `0x0044fa80` karakterlánc-bemenetet kezel, de a törzsében az `esi += 0xd50` után olvas `[esi+0x58]`-at (`0x0044fac1`, `0x0044fb07`): ez a függvény fogadómutatójához képest `+0xda8`. A dátumlekérdező `0x0044f7c0` ezzel szemben az `esi += 0xbc8` után olvas `[esi+0x58]`-at (`0x0044f80f`, `0x0044f857`), azaz a saját fogadómutatójához képest `+0xc20`; a Ghidra-kimenet ugyanezt `param_1+0xc20` alakban mutatja. Ezért a `0x0044fa80` nem azonosítható a dátumlekérdező `+0xc20` tárolójának írójaként. A dátumlekérdező `+0xc20` pointerének/tömbjének írója, a qword-elemek jelentése, sorrendje és teljessége továbbra is **NINCS MEG**. A meglévő `2026-11-05-idorend-6532-datumformazo.txt` a gettert dekompilálja, az író útját nem; a `0x0044fa80`-ról nem találtam kész Ghidra-dekompilátumot.

Az indextől független, memóriakapus `paszta.py` keresés a `+0xc20`, `+0xbc8`, `+0xc68`, `+0xd50` és `+0xda8` operandusokra 56 találatot adott. Ezek közül például a `0x006ba4a0` inicializáló a `ytCachedImage::vftable` (`0x00ca85a4`) osztályához tartozik, ezért nem a dátumgetter CThumbDB-adatútjának bizonyítéka. Az azonos numerikus eltolások más osztályokban és veremhelyeken is előfordulnak; ebből a keresésből nem nevezhető meg és nem zárható ki a `+0xc20` mező CThumbDB-írója.

- Ghidra-kör kell: 0x0044f7c0 - a függvény `this+0xc20` pointerének/tömbjének írója és a qword-kulcs pontos naptári jelentése. A meglévő `2026-11-05-idorend-6532-datumformazo.txt` csak a getter 64 bites elemolvasását mutatja; az író és a kulcs jelentése nincs benne. A rendezési irányt és a descriptorok két szűrési feltételét a 38.2.105 már binárisból rögzíti, azokat nem kérjük újra. [blokkoló]

#### 38.2.104 A job-446 képkockahatárai és a leütés-hozzárendelés (#6532, 2026-11-08)

**Állapotfrissítés (2026-11-10):** a két preferencia beolvasási alapértéke binárisból lezárva (38.2.105); a job-446 tényleges registry-értékei, a +0x520 QPC-kezdőérték, a pontos képkockahatár és a billentyű-időbélyegek továbbra is nyitottak.

**Kérdés és következtetés.** A job-446 videóban mérhető három kártyacsomag-változás első képkockája, a fő geometriai elmozdulás, a felület képpontváltozásának burka és a kártyák pályája. A videó nem tartalmaz billentyűesemény-időbélyeget; a feladatleírás névleges leütései és az eseményképek nem rendelhetők egyértelműen a folyamatos felvétel mozgási képkockáihoz. Ez a szakasz ezért a videón látható intervallumokat rögzíti, nem állít közvetlen billentyű-okozatot.

**Forrás és módszer.** A picasa-colab-jobs #446 felvétele (`video__04.mp4`) H.264, 1280×1024 képpontos, 15 fps és 720 képkocka hosszú (`ffprobe`, 48,000 s). A képkocka `n` időpontját `n/15` s adja; a mintaköz 66,666… ms. Minden képkockát dekódoltam. A qshow-lap ROI-jában (`x=320-959`, `y=240-784`, képernyő-koordináta) az egymást követő szürke képek abszolút különbségét számoltam. Változás-burkot akkor jelöltem, ha egy képkockapárban 100-nál több ROI-pixel intenzitáskülönbsége nagyobb 1-nél. A kártyasáv külön `>8` intenzitásküszöbű változó-pixelszámlálását színenkénti HSV-befoglaló dobozokkal ellenőriztem. A dobozok `x,y` koordinátája a 600×480-as qshow-lap bal felső sarkához relatív (képernyőn a lap bal felső sarka `340,272`). A kártyasáv-küszöbben legfeljebb egy változatlan képkockával elválasztott szakaszokat az első-utolsó burokhoz vontam össze; az izolált kiugrás nem önálló átmenet.

**Mért képkockák.** A táblázatban a „végponttávolság” az első és utolsó jelölt képkocka időpontja közötti különbség; a „mintafedés” az inkluzív képkockaszám osztva 15-tel. Egyik sem állít a 66,7 ms-os mintaköznél finomabb időpontot.

| Változás | Küszöbölt képkockák | Végponttávolság; mintafedés | A látható geometria |
|---|---:|---:|---|
| Qshow megjelenési átúszás | `n=96-119` | 1533,3 ms; 1600 ms | A qshow-lap fokozatosan válik láthatóvá. A feladat 2 s-os Ctrl+5 idejéhez való pontos eltérés a videóban NINCS MEG. |
| 1. kártyacsomag-váltás | a kártyasáv változásának tartománya `n=263-285`; befoglaló dobozok pályája mintái `n=263→281` | 1466,7 ms; 1533,3 ms a küszöbölt burokra; 1200 ms a befoglaló doboz mintapárja között | A csomag balra halad; a negyedik, sárga doboz a menetben jelenik meg. A jobb felső csoportfelirat `n=267`-re 2014. |
| 2. kártyacsomag-váltás | a kártyasáv változásának tartománya `n=410-432`; befoglaló dobozok pályája mintái `n=410→428` | 1466,7 ms; 1533,3 ms a küszöbölt burokra; 1200 ms a befoglaló doboz mintapárja között | A négyes csomag ismét balra halad. A jobb felső csoportfelirat `n=414`-re 2019. |
| 3. kártyacsomag-váltás | a kártyasáv változásának tartománya `n=565-586`; befoglaló dobozok pályája mintái `n=565→584` | 1400 ms; 1466,7 ms a küszöbölt burokra; 1266,7 ms a befoglaló doboz mintapárja között | A csomag jobbra tér vissza a korábbi elrendezéshez. A jobb felső felirat `n=569`-re 2014. |

A „kártyasáv változásának tartománya” a `>8` intenzitású eltérő pixelek 100 pixeles számláló-küszöbe szerinti első-utolsó képkocka; az egyetlen képkockás lyukakat összevonja. A befoglaló dobozok pályája `n=281`, `n=428` és `n=584` mintái a fő áthelyezett elrendezést mutatják. A pixelburok néhány képkockával tovább tart, mert a kártyakép tartalma és a környező felület is változik. Emiatt a fizikai elmozdulás utolsó, egyetlen képkockára pontos határa **NINCS MEG**; a befoglaló doboz mintapárjai és a küszöbölt burkok külön mérési eredmények.

**A fő elmozdulás színdobozai.** A koordináták a színmaszkok bal felső `x` pontjai, képpontban; a `nincs` azt jelenti, hogy az adott színű dobozt a maszk az átmenet előtt nem találta.

| Váltás | Előtte (`n`) | Utána (`n`) | `dx` a piros/kék/zöld/sárga dobozokra |
|---|---|---|---|
| 1. | `364,456,536,nincs` (`262`) | `270,362,456,540` (`281`) | `-94,-94,-80, új doboz` |
| 2. | `268,360,456,540` (`409`) | `186,266,362,460` (`428`) | `-82,-94,-94,-80` |
| 3. | `186,266,360,458` (`564`) | `268,360,454,540` (`584`) | `+82,+94,+94,+82` |

A dobozok `y` koordinátája is változik: az 1. váltás előtt/után a piros-kék-zöld-sárga `y` sor `332,319,296,nincs` → `322,322,312,306`; a 2.-nál `320,322,314,306` → `298,313,318,324`; a 3.-nál `298,312,318,324` → `320,324,314,306`. Ez forgó, a képernyő síkjára vetülő csomagmozgással egyezik; a mintavétel nem igazol hozzá folytonos pályaképletet vagy időfüggvényt.

**A teljes lap külön mért változása.** A qshow-lap ROI-jában a `>1` intenzitáskülönbségű, 100 pixelt meghaladó képkockapárok első-utolsó tartományai: `263-316` (3533,3 ms végponttávolság, 3600 ms mintafedés), `410-463` (ugyanez), `565-616` (3400 ms végponttávolság, 3466,7 ms mintafedés). A `n=619` különálló változása nem folytonos része a harmadik buroknak. Ez a mérőszám a kártyát, hátteret, feliratot és felületet együtt tartalmazza; nem azonos a háttérkeverő belső progressziójával.

**Leütések és második ellenőrzési út.** A `feladat.md` névleges leütési idejei Ctrl+5 `2 s`, Right `10 s`, Right `16 s`, Left `22 s`, Right `28 s`, Escape `36 s`. A külön munkafolyamat-képek (`kepernyo__08-16.png`) az utána rögzített feliratállapotokban a 2009 → 2014 → 2019 → 2014 → 2019 sorrendet mutatják. Ez független ellenőrzés a videó képkockáin látott csoportnevekre, de nem ad hozzá videóképkocka-pontosságú billentyű-időbélyeget. A videó átmenetkezdetei közötti különbség 147, illetve 155 képkocka (9800, illetve 10333,3 ms), miközben a névleges nyíl-leütések 6 s távolságra vannak. A videón a qshow a 719. képkockán (47,933 s) még látható; az `allapot.json` 17. lépése qshow nélküli állapotot jelez. A két út ezért **nem** támasztja alá a billentyű és a mozgás közvetlen egy-az-egyhez párosítását, sem az automatikus léptetést.

**Bináris időalap és PicasaPy-összevetés.** A qshow konstruktor `0x007fa7f0` a `SlideshowEffectTime` alapértékét `3`-ra állítja (`0x007facd3`), és a `Preferences` kulcshoz köti (`0x007facdb-0x007facec`). A `0x008001c0` a `SimpleSlideshow` kulcsnál `1` alapértéket állít (`0x00800297-0x008002be`). Ezek a PE közvetlen utasításolvasatából származó alapértékek; a 446-os futás futásidejű Preferences-tartalma és a `+0x520` QPC-kezdőérték **NINCS MEG**. A 38.2.100 szerint az alapértékek feltételezése mellett a `3 s` progresszióbemenet `1,5`-szöröse `2 s`-nál telítődik. A most mért 1200-1266,7 ms fő kártyamozgás és 3400-3533,3 ms teljes-lap változás egyik belső idővel sem azonosítható: a kártyapálya és a teljes ROI nem ugyanaz a bináris progressziómérő.

| Eredeti Picasa | PicasaPy-forrás (nem futásidejű mérés) | Teendő |
|---|---|---|
| A #446 küszöbölt kártyasáv-burok végponttávolsága 1466,7, 1466,7 és 1400 ms; a befoglaló dobozok pályája végpontmintáinak távolsága 1200, 1200 és 1266,7 ms. A teljes lap változása 3533,3, 3533,3 és 3400 ms. A fizikai utolsó mozgó frame és a billentyű-kapcsolat nyitott. | A `TimelineView.qml:106-115` egy `step()` hívásnál 2000 ms időtartamú animátorrekordot hoz létre; a `:333-379` 16 ms-os Qt-timert és külön kártya/háttér módot használ. A `:43-45` háttérátúszása 1400 ms-ra van állítva. Ezek forrásparaméterek, futásidejű mozgásmérés nélkül. | A 2000 ms-os kártya- és 1400 ms-os háttérparamétert külön, azonos 15 fps-es PicasaPy-képfelvételben kell mérni, szinkronizált billentyű-időbélyeggel. A megváltozott értéket csak akkor kell az eredetihez igazítani, ha a mért fő kártyamozgás ugyanarra az `step()` útvonalra rendelhető. A jelen videóból pontos kódérték-módosítás nem igazolt. |

**A két út és bizonyítottsági fok.** A út: a 720 dekódolt képkocka egymás utáni ROI-különbsége és a színmaszkos kártyák befoglaló dobozai adják a frame-szintű burkokat, az irányt és a koordinátaváltozást. B út: a munkafolyamat külön `kepernyo__NN.png` képei és állapotlistája a látható gyűjtemények sorrendjét ellenőrzi. A két út a 2009/2014/2019 feliratváltásokat alátámasztja, de a képkockahatárokhoz csak az A út ad folyamatos időmérést; a leütés-képkocka-kapcsolat eltérő, ezért **feltételes**.

**Cáfoló kísérlet.** Megpróbáltam cáfolni, hogy a három mozgás mindegyike a közvetlenül előtte naplózott nyíl-leütésből ered. Az első-utolsó átmenetkezdések 147 és 155 képkockára vannak egymástól; a harmadik a névleges Escape után indul, és a videó végéig látható marad, miközben a külön állapotfájl már zárt qshow-t jelez. A képkocka-mérőt ugyanazzal a szürke-differencia és >100 pixeles kritériummal ellenőriztem; az egyetlen n=619 kiugrást nem tekintettem új, folyamatos átmenetnek. Az ellenpélda a közvetlen leütés-hozzárendelést cáfolja, de nem bizonyít automatikus lejátszást.

**A #6532 „Kész, ha” pontjai.**

1. ✅ Van eredeti Időrend-videó: a helyi job-446 MP4 48,000 s, 720 képkocka; a teljes képsor elemzése elkészült.
2. ⛔ A teljes működés minden pontja még nincs bináris címmel igazolva. A képkocka-burkok méréssel ismertek, de a valódi Preferences-érték, `+0x520`-hoz viszonyított alpha, a billentyű-képkocka szinkron és a fizikai utolsó mozgó képkocka nyitott.
3. ⛔ A PicasaPy-forrással a mozgási időparaméterek össze lettek vetve, de futásidejű, összehasonlítható PicasaPy-felvétel nélkül pontos megvalósítási eltérés nem igazolt. A megvalósítási jegy #6713 létezését a feladatleírás adja meg; GitHub-állapotát ebben a körben nem ellenőriztem.
4. ⛔ Kiadási összehasonlító videó/képsor még nincs elkészítve.

**Nyitott és következő mérés.** A job-446 MP4 és a lépésképek billentyű-időbélyegeit ugyanarra a monotón időalapra kell venni (a következő rögzítésen képkockára égetett eseményjelölővel); ugyanabban a Wine-futásban el kell menteni a `SlideshowEffectTime` és `SimpleSlideshow` tényleges Preferences-értékét, valamint a qshow `+0x520` kezdeti QPC-jét. Ez dönti el, hogy a 3 s-os bináris progresszió és a 1400/2000 ms-os PicasaPy-forrásparaméterek ténylegesen összehasonlíthatók-e. A `CThumbDB+0x48` `+0x20` által visszaadott dátumtömb feltöltője/sorrendje és teljessége, valamint a PicasaPy `records` halmazával való azonossága továbbra is a 38.2.103 nyitott kérdése.

#### 38.2.105 A #6532 lezárási mérlege (2026-11-10)

**Következtetés.** Az eredeti Időrendről van job-373 és job-446 videó. A kártyák megjelenítési modellje, a jobb felső feliratok, a dátumvonal és a beállítások bináris alapértéke dokumentált; a qshow kártyalistáját a bináris dátum-qword szerint növekvő sorrendben építi. A teljes CAlbumState-forráshalmaz, a szűrők jelentése, a PicasaPy gyűjteményekkel való futásidejű azonosság és az átmenetek billentyű-képkocka kapcsolata nyitva marad. Megvalósítási eltérés ezekből nem állapítható meg.

**Állapotjelölések.** A „bináris” az eredeti Picasa3.exe utasítás- vagy adatcímét jelenti; a „mérés” a megnevezett videó vagy képsor közvetlen elemzését; a „NINCS MEG” nem becslés, hanem nyitott kérdés és megszerzési út.

| Pont | Állapot | Bizonyított eredmény / nyitott rész | Szakasz |
|---|---|---|---|
| Eredeti Időrend-videó | mérés (job-373 és job-446) | Mindkét videó helyben elérhető; a job-446 teljes felvételét a 38.2.104 elemzi. | 38.2.101, 38.2.104 |
| Lap mérete | bináris (0x007fa730) | Az Időrend gombja 480 px magas, képernyőarányos lapot kér. | 38.2.98 |
| Kártyák pályája, láthatósága és mélységi alfája | bináris (0x007fc010, 0x007fd180, 0x00cf3ef8, 0x00cf3ec4) | A 3D pálya, Z > 0.1 szűrő, alfa-képlet és a nyitó alfa útja leírt. | 38.2.102 |
| Kötegen belüli szórás | HELYESBÍTVE (38.2.150) | A `0x008014d0` kapuzott rejtett módú függvény (`Ctrl+F`/`Ctrl+B`), helyzet- és sebességmezőket ír; a régi "kártyaeltolás" olvasat megdőlt. | 38.2.150 |
| Bélyegkép-forrás és háttér | bináris (0x00424b10, 0x00802180, 0x008001c0) | A háttér a középső kártya képéből készül; a szolgáltató legalább 640 px-es forráságát a korábbi kör azonosította. | 38.2.94, 38.2.97 |
| Dátum-idő felirat és ferde csíkok | mérés (job-373 mintakép és 2009_majus_01.jpg) | A felirat és a csíkozás a mintakép része, nem a qshow felület rajzolja rá. | 38.2.93 |
| Jobb felső felirat és vezetőív | bináris (0x007fee70, 0x00cf4e8c, 0x00cf4e88, 0x00cf3bd8) | Név y=130, hónap-év y=158, 1 px fekete árnyék, 10 pontú Bézier-ív. | 38.2.102 |
| Qshow kártyalista rendezése | bináris (0x007fc7c0, 0x007fc4c0, 0x0049cd60) | A két feltétellel megtartott CAlbumState-leírók 64 bites dátumkulcsát növekvően rendezi, majd ezekből készülnek a 0xf8 bájtos qshow-rekordok. | 38.2.105 |
| A qshow-lista forráshalmaza és szűrőinek jelentése | NINCS MEG | A bemeneti lista elemszáma és két megtartási feltétele ismert; a teljes könyvtár/mappa/album/virtuális csoport lefedettség és a mezők jelentése nem. | 38.2.105 |
| A qshow-descriptorok lehetséges upstream építőútja | feltételes (bináris 0x004b8470, 0x004b29d0, 0x004ae600) | A `0x004b8470` üríti a `+0x158/+0x15c` listát, a `+0x148/+0x14c` bemeneten iterál és `0x004b29d0`-t hív; az utóbbi a `+0x48`-on elért CAlbumState `+0x138/+0x13c` rekord `+0x0c == 2` értékét ellenőrzi, majd 56 bájtos rekordot másol. A teljes pointerlánc a qshow `[this+0xac]` bemenetéhez és a rekordmezők tartalmi jelentése NINCS MEG. | 38.2.105 |
| A dátum-qword tömb írója és naptári jelentése | NINCS MEG | A `0x0044f7c0` getter a `+0xbc8`-on át elért `+0x58` tömbből qwordot ad vissza, tartalék értéke a `+0x60`; a `0x00477920` hasonló alakú, de más (`+0x1a48`) tárolót ír, ezért nem azonosított író. | 38.2.105 |
| Qshow-lista és PicasaPy-gyűjtemények azonossága | NINCS MEG | A PicasaPy forrása: nem rejtett fotókból mappakártyák, valamint nem üres, indexelt albumokból albumkártyák; a gyűjtemények kulcsa a legkorábbi tag EXIF-dátuma, név és azonosító. Ez a forráskód-tény nem bizonyítja a qshow-listával való futásidejű azonosságot. Forrás: timeline_controller.py:183-264, index/queries.py:187-199, index/albums.py:142-198. | 38.2.105 |
| SlideshowEffectTime alapértéke a beolvasásnál | bináris (0x007fa7f0, 0x007facd3, 0x007facdb-0x007facec) | A beolvasás előtt 3 kerül az alapérték-struktúrába. | 38.2.104 |
| SimpleSlideshow alapértéke a beolvasásnál | bináris (0x008001c0, 0x00800295-0x008002be, 0x00800620-0x00800643) | Mindkét beolvasási út előtt 1 az alapérték. | 38.2.104 |
| A videó tényleges Preferences-értékei | NINCS MEG | A fenti bináris alapérték nem bizonyítja, mit olvasott a job-446 futás. | 38.2.104 |
| Billentyű és mozgó képkockák pontos kapcsolata, fizikai utolsó képkocka | NINCS MEG | A videó burkai mérve vannak, de nincs hozzájuk szinkron billentyű-időbélyeg. | 38.2.104 |
| PicasaPy-val összehasonlítható futás és release-képsor | NINCS MEG | Ehhez azonos képkészlet, rögzített Preferences, szinkron eseményjel és összehasonlító videó/képsor kell. | 38.2.104 |

**Eredeti / nálunk / teendő.**

| Eredeti Picasa | Jelenlegi PicasaPy | Teendő |
|---|---|---|
| A köteg szórása a CRT rand kimenetéből jön (0x008014d0); a jobb felső név/dátum pozíciója és árnyéka, valamint a 10 pontú vezetőív képlete binárisból ismert (0x007fee70). | A #6713 utáni forrás ugyanazt a szórási tartományt index-alapú, stabil xorshift PRNG-vel valósítja meg (timeline_motion.py:100-162); a QML a mélységi alfát, feliratpozíciókat, árnyékot és vezetőpontokat alkalmazza (TimelinePanel.qml:137-148,208,335-398). | A tartomány és a geometriai modell forráskód szerint megfelel. Az eredeti seed és futásidejű képkockapozíció nincs mérve, ezért a PRNG-különbségből nem igazolt felhasználói eltérés; új implementációs teendő nem következik. |
| A qshow bemeneti descriptorait két feltétel szűri, majd dátum-qword szerint növekvően sorolja (0x007fc7c0, 0x007fc4c0, 0x0049cd60). A job-239 képsor négy dátumos mappát növekvő felirat-sorrendben mutat. | A PicasaPy mappa- és albumkártyákat állít elő; mindegyik dátuma a legkorábbi tag EXIF-dátuma, a teljes kártyasorrend kulcsa dátum, név, azonosító (timeline_controller.py:217-264,321-335). | Az irány egyezik a felvételen látható négy mappán, de a két teljes descriptorhalmaz azonossága és a qshow kulcs naptári jelentése NINCS MEG. Fejlesztői rendezés-javítás ebből nem igazolt. |
| A job-446 képen mért kártyacsomag-változás fő dobozpálya-mintái 1200-1266,7 ms-ra esnek; a küszöbölt teljes kártyasáv-burok 1400-1466,7 ms-os végponttávolságú. | A QML carousel animátor 2000 ms-ot kap lépésenként, a háttérforrás 1400 ms-ot állít be (TimelineView.qml:43-45,106-115). | A mérőszámok és a QML animátor ideje nem ugyanaz az eseményhatár. Szinkron, azonos képkészletű PicasaPy-felvétel nélkül pontos időzítési kódmódosítás nem igazolt. |

**A két független út.**

- A út - bináris: a 0x007fc7c0 leírja a bemeneti descriptorok két feltétel szerinti megtartását és a rendezőhívást; a 0x007fc4c0 és 0x0049cd60 külön utasításútja a 64 bites qword-kulcs növekvő összehasonlítását végzi. A 0x0044f7c0 dátumlekérdezővel összekötve a rendezési kulcs dátum-qword.
- B út - mérés: a job-239 külön képsorán a 2009, 2014, 2019 és 2021 feliratú mappák időrendi sorrendben jelennek meg; a job-373/446 videók nem mutatnak ezzel ellentétes látható sorrendet. Ez a mérés a látható mappák sorrendjét ellenőrzi, de nem igazolja a teljes listát vagy a descriptorok azonosságát.
- Egyezés: a rendezés bináris iránya és a felvételen látható csoportsorrend nem mond ellent egymásnak. A forráshalmaz teljessége és PicasaPy-egyezése nyitott, tehát a teljes halmazra vonatkozó megfelelés nem megerősített.

**Bizonyítottsági fok.** **Megerősített** a qshow dátum-qword szerinti növekvő rendezési mechanizmusa: a kártyaépítő/rendező utasításút és a külön videóképsorokon látható dátumos csoportsorrend egyezik; a videó csak a megfigyelt csoportokra érvényes. **Nyitott** a teljes forráshalmaz, a szűrők jelentése, a qword naptári pontos jelentése, a PicasaPy-listával való azonosság és a billentyű-képkocka-időzítés. A #6532 teljes lezárási mérlege ezért **nyitott**.

**Cáfoló kísérlet.** Megpróbáltam cáfolni, hogy a qshow kártyák csak a CAlbumState bemeneti sorrendjét öröklik. A teljes .text pásztázás előtt a kötelező paszta.memoria_kapu() futott; a qshow alobjektum +0xb0/+0xb4 mezőire külön célzott keresés vezetett a 0x007fc7c0 builderhez. A builder dátum-qwordokat készít és meghívja a rendezőt, ezért a bemeneti sorrend változtatás nélküli másolata cáfolt. A 0x008018a0 által épített kiválasztott gyűjtemény képlistája külön +0x3ec mező, nem bizonyíték a +0x3a8 descriptorlistára. A cáfoló kör mércéje ugyanaz maradt: csak az osztályhoz kötött utasításút és a célzott mező-hozzárendelés számított pozitív leletnek; az indextalálat vagy más osztály azonos offszetje nem.

**2026-11-10-i célzott utánkövetés és második cáfoló próba.** A memóriakapuval védett `.text`-pásztázás pozitív kontrolljai (`0x0044f80f`, `0x007fc85f`, `0x007fca18`) megvoltak. A qshow-szűrők upstream útja `0x004b8470` → `0x004b29d0` → `0x004ae600` címekre szűkült, de a pointertípus és a qshow-descriptorral való azonosság nincs meg. A dátumgetter utasításszinten `0x0044f80f`-nél a `+0xbc8` objektumot választja, majd `0x0044f857`-nél annak `+0x58` tömbmutatóját olvassa, végül a `+0x60` qwordra esik vissza. Megpróbáltam a `0x00477920` CThumbDB-vtáblamódszert a keresett íróként azonosítani: a `0x0049f420` thunk és a függvény diszasszemblálása a `this+0x1a48+0x58` tömb írását mutatja, nem a getter `this+0xbc8+0x58` láncát; az azonosságot ezért nem fogadtam el. A jelölt elutasítását nem az index hiányára, hanem az operandusok kapuzott pásztázására és a két módszer utasításláncának összevetésére alapoztam; a tényleges író ettől továbbra is nyitott.

**A #6532 „Kész, ha” pontjai (a 2026-11-10-i szűkített feltétel).**

1. ✅ Van eredeti Időrend-videó: job-373 és job-446, mérés a 38.2.101 és 38.2.104 szakaszban.
2. ⛔ A megvalósításra releváns leírópontok részben címzettek, de a qshow-forráshalmaz/szűrők, a PicasaPy-egyezés és a futásidejű mozgásbeállítások NINCS MEG állapotban maradnak. A feltétel ezért még nem teljesül.
3. ⛔ A #6713 a tulajdonos jegyszövege szerint lezárult. A mostani körben nincs bizonyított, fejlesztői teendőt indokoló maradék eltérés, így új implementációs jegy kész szövege felelősen nem adható. A feltétel - nyitott megvalósítási jegy - jelenleg nem teljesül.
4. ⛔ Kiadásba adható, PicasaPy-val párhuzamos összehasonlító videó vagy képsor ebben a kutatási körben nem készült.

**Külön kutatási jegyjavaslatok.**

1. **Az Időrend qshow CAlbumState-listájának pontos forráshalmaza.** Kérdés: mely mappák, albumok és speciális/virtuális csoportok kerülnek a 0x007fc7c0 bemeneti descriptorlistájába, mit jelentenek a 0x004ae4e0 eredményének local_10c==1 és local_124==0 feltételei, és ugyanazt a gyűjteményhalmazt állítja-e elő a TimelineController? Keresd a 0x005e942e → CAlbumState+0x15c és 0x007fc7c0 → 0x004ae4e0 útját; vesd össze a job-239/job-373 videóval és a timeline_controller.py:183-264 forrással.
2. **Az Időrend átmeneteinek képkocka-pontos időzítése.** Kérdés: a tényleges SlideshowEffectTime és SimpleSlideshow érték, a qshow +0x520 időalap és a külön leütések mely első/utolsó mozgó képkockához tartoznak? Keresd a 0x007facd3 és 0x00800295/0x00800620 beolvasási útját; job-446 mellé kérj olyan új Wine-felvételt, amelyben a billentyűesemények időbélyege és a beállítások ugyanahhoz a monotón órához kötöttek.
3. **Az Időrend kártyaszórásának seedje és ismétlési viselkedése.** Kérdés: melyik út inicializálja a CRT rand állapotát a 0x008014d0 hívásai előtt, és azonos fotókártyák pozíciói azonosak-e külön qshow-indítások között? Keresd a bináris rand- és seedíró hívásokat, majd ismételt eredeti Wine-futásban mérd a kártyaeltolásokat. A PicasaPy indexmagos xorshift-algoritmusát addig ne minősítsd felhasználói eltérésnek pusztán a forráskülönbség alapján.

**Nyitott.**

- Ghidra-kör kell: 0x004b8470 - az upstream listák (`+0x148/+0x14c`) típusa, a `0x004b29d0` hívási argumentumai, a két qshow-megtartási mező forrása és a qshow `[this+0xac]` descriptorlistájához vezető pointerlánc. A meglévő `0x007fc7c0` és `0x004b29d0` dekompiláció ezek tartalmi jelentését/azonosságát nem válaszolja meg. [blokkoló]
- Ghidra-kör kell: 0x0044f7c0 - új kérdés a meglévő 2026-11-05-i getter-dekompilációhoz: melyik CThumbDB-út tölti a `this+0xbc8+0x58` qwordtömböt, és a qword milyen pontos naptári reprezentációt és gyűjteménydátumot hordoz? A `0x00477920` hasonló tömbíró, de a jelen diszasszemblálás `this+0x1a48+0x58` tárolót mutat; a kapcsolatot a meglévő kimenet nem dönti el. [blokkoló]
- A job-446 tényleges Preferences-értékei és a +0x520 frissítési időalapja NINCS MEG; megszerzésükhöz az eseményekkel szinkron új Wine-videó és ugyanabban a futásban rögzített beállítások szükségesek.

**Módosított fájlok ebben a szakaszban.** A 38.2.105-ös mérleg a 2026-11-10-i helyi diszasszemblálás eredményeivel bővült; az összevető táblák PicasaPy-kódreferenciái nem futásidejű mérések.

#### 38.2.106 A bemeneti lista hívási hídja és a dátumtömb nyitott írója (#6532, 2026-11-10)

**Hatókör.** A `0x004b8470` upstream listáját a `0x006dc4c0` hívó felől ellenőriztem, és újraértékeltem, összeköthető-e a qshow bemenetével. A dátumgetter `0x0044f7c0` íróját célzottan kerestem a helyi `.text`-ben és a CThumbDB RTTI-vtable metódusai között. A kör nem futtatott Picasát és nem módosított termékkódot.

**A hívási út.** A `0x006dc4c0` a `[esp+0x68]` értékét `EBP`-be tölti (`0x006dc4c5`), majd a `[EBP+0x2c0]` értéket adja `EAX`-ban a `0x004b8ee0`-nak (`0x006dc626`-`0x006dc62c`). A `0x004b8ee0` meghívja a `0x004b8470`-et (`0x004b9192`); a `0x004b8470` pedig a megtartott indexek feldolgozásakor a `0x004b29d0`-t hívja (`0x004b85c8`). A bináris-index xref-jei ugyanezt a függvényláncot adják: `0x006dc4c0 → 0x004b8ee0 → 0x004b8470 → 0x004b29d0`.

**A lista és a szűrés tényleges határa.** A `0x004b8470` a `[this+0x148]` dword-tömb `+[index*4]` értékét olvassa; a ciklusszám a `[this+0x14c] >> 1`. Ha a `[this+0x9d]` bájt nem nulla, a `0x004461a0` kapja a `[this+0xc4]` értéket és az aktuális indexet, és a hamis eredmény kihagyja a `0x004b29d0` hívását. A feltétel tartalmi jelentése NINCS MEG. A `0x004b29d0` a CAlbumState-ként korábban azonosított objektum `[+0x138 + index*0x24 + 0x0c]` mezőjét `2`-höz hasonlítja, majd a `0x0044ddd0` segítségével további elemet kér; a mező szemantikája szintén NINCS MEG. A `0x004b8470` által épített rekord `0x38` bájtos (`push 0x38`, `0x004b8568`); a qshow `0x007fc7c0` builderének kártyarekordja `0xf8` bájtos. Ez kizárja, hogy a két rekordlista ugyanaz a nyers puffer legyen, de nem zárja ki köztük az adaptert.

**A qshow-val való kapcsolat.** A `CThumbUI+0x2c0` `CAlbumState` pointerét a 38.2.69 két külön úton azonosítja; a qshow elemlekérője a külön `CThumbUI+0x2bc` szolgáltató `+0x20` virtuális helyére jut (`0x00562cc0`). A mostani híd `0x006dc4c0`-ban ugyancsak numerikusan `+0x2c0`-ról olvas, de a függvény `[esp+0x68]` objektumának osztálya és a mező típusa nincs azonosítva. Ezért az azonos eltolás nem bizonyítja, hogy ugyanarról a CAlbumState-ról van szó; a `0x004b8470` kimenetének qshow `[this+0xac]` bemeneti leíróihoz vagy a qshow szolgáltatójához vezető útja továbbra is NINCS MEG.

**A dátumtömb.** A `0x0044f7c0` getter `0x0044f80f`-nél a `this+0xbc8` alobjektumra lép, `0x0044f857`-nél annak `+0x58` tömbjéből olvas, és hiányzó elemnél a `+0x60` qwordot adja vissza. A korábban vizsgált `0x00477920` másik, `this+0x1a48+0x58` tárolóba ír; ezért nem a keresett író. A kapuzott teljes `.text`-pásztázás és a CThumbDB RTTI-vtable metódusain futtatott `offset_map.py` nem adott osztályhoz kötött írócímet. Az utóbbi korlátozott negatív eredmény (regiszterfelismerési és RTTI-lefedettségi határral), nem bizonyíték arra, hogy nincs író. A pontos tömbíró és a qword naptári jelentése NINCS MEG.

**Bizonyíték és bizonyítottsági fok.**

| Állítás | Forrás | Fok |
|---|---|---|
| A hívási lánc `0x006dc4c0 → 0x004b8ee0 → 0x004b8470 → 0x004b29d0`. | bináris (`0x006dc626`, `0x004b9192`, `0x004b85c8`) + xref (`binary-index/xrefs`, meglévő Ghidra-hívólista) | megerősített a függvényhívásokra |
| A `0x006dc4c0` bemeneti objektumának `+0x2c0` mezője `CAlbumState`, illetve ez a qshow-lista forrása. | NINCS MEG | nyitott |
| A `0x004b8470` ciklusmezői, opcionális szűrőhívása és `0x38` rekordépítése. | bináris (`0x004b8470`, `0x004b29d0`, `0x004ae600`) | feltételes; az utasításút olvasható, a mezők jelentése és osztálya nem |
| A `0x0044f7c0` getter által olvasott `+0xbc8+0x58` tömb írója és a dátum qword naptári jelentése. | NINCS MEG | nyitott |

**A két független út.** A út: az eredeti PE függvényenkénti utasításolvasása mutatja a `[EBP+0x2c0]` adatátadást és a következő közvetlen hívásokat. B út: a bináris-index xref-táblája és a már meglévő `2026-10-21-idorend-25.txt` hívói és hívott függvényeinek listája külön is ugyanazt a függvényláncot sorolja fel. A két út egyezik a hívási kapcsolatokban. Az objektum osztályára, a mező típusára és a qshow-listával való azonosságra egyik út sem ad bizonyítékot, ezért ezek nem megerősített állítások.

**Cáfoló kísérlet.** Azt a hipotézist próbáltam cáfolni, hogy a `0x004b8470`-ben épített `0x38` bájtos rekordlista maga a qshow `0xf8` bájtos kártyalistája: a rekordméretek eltérnek (`0x004b8568`, illetve `0x007fc7c0`), tehát a nyers pufferazonosság nem tartható. Ez a cáfoló próba ugyanazzal a mércével közvetlen gépi kódot vizsgált; egy köztes átalakítót nem cáfol. A dátumíró jelöltjeként próbáltam elfogadni a `0x00477920`-at is, de a függvény másik `+0x1a48+0x58` tárolót ír, nem a getter `+0xbc8+0x58` útját. A kapuzott pásztázás pozitív kontrolljai megvoltak; a CThumbDB `offset_map.py` negatív találatát nem tekintettem globális bizonyítéknak.

**A #6532 „Kész, ha” pontjai.** (1) ✅ Eredeti videók: a job-373 és job-446 helyi felvételeit a 38.2.101 és 38.2.104 dokumentálja. (2) ⛔ A teljes működés minden megvalósítandó pontja nincs bináris címmel igazolva: a forráshalmaz, szűrőszemantika, qshow-azonosság, dátumtömb írója és több futásidejű beállítás nyitott. (3) ⛔ Ebből a körből nem következik új, bizonyított fejlesztői eltérés; a #6713 tulajdonosi jegyszöveg szerinti lezárása nem igazolja a teljes #6532 feltételt. (4) ⛔ PicasaPy-val összehasonlító, kiadásba adható videó/képsor nincs dokumentálva.

**Nyitott.**

- Ghidra-kör kell: 0x006dc4c0 - a `[esp+0x68]`-ről érkező objektum osztálya és a `+0x2c0` mező tagtípusa; a meglévő Ghidra-kimenet csak a `0x004b8ee0` hívási xref-jét sorolja fel, a teljes `0x006dc4c0` dekompilációt nem tartalmazza. [blokkoló]
- Ghidra-kör kell: 0x004b8470 - a 38.2.105-ben jelzett kérés pontosítása: a `+0x148/+0x14c` lista típusa, a `[this+0x9d]`/`+0xc4` szűrés szemantikája, és van-e átalakító út a `+0x158` `0x38` rekordlistától a qshow `[this+0xac]` bemenetéhez vagy a `CThumbUI+0x2bc` szolgáltató `+0x20` helyéhez. A meglévő `0x004b29d0` dekompiláció ezekre nem válaszol. [blokkoló]
- A dátumtömb írója és naptári jelentése a 38.2.105-ben már nyitott Ghidra-kérdés; a jelen kör nem talált új írót. A megszerzési út változatlan: a `0x0044f7c0` getter hívóinak és a CThumbDB betöltő/vtable útjainak visszakövetése.
- A `0x004b29d0` által vizsgált `+0x0c==2` mező, a `0x004461a0` predikátum és a teljes qshow-bemeneti halmaz jelentése NINCS MEG; megszerzési út: a fenti célzott Ghidra-kör, majd a builder és a CThumbUI szolgáltató közti közvetlen pointer-/vtable-adatút végigkövetése.
- A dátumtömb írója NINCS MEG; megszerzési út: a `0x0044f7c0` beolvasási útjának hívóitól és a CThumbDB vtable-adatútjaitól a `+0xbc8+0x58` írásáig visszakövetés, majd az író osztályhoz kötésének ellenőrzése.

**Módosított fájlok ebben a szakaszban.** Ez a 38.2.106-os utánkövetés csak a kutatási specet és annak indexleírását bővíti; nincs új PicasaPy-futásmérés, kódváltozás vagy új implementációs eltérés.

#### 38.2.107 A dátumoszlop írója és a qshow-híd nyitott határai (#6532, 2026-11-11)

**Hatókör.** A friss Ghidra-kimenetek és a binárisból végzett célzott, memóriakorlátos diszasszembly alapján követtem a `0x0044f7c0` dátumgetter `+0xbc8+0x58` útját, valamint a `0x006dc4c0`-ból induló CAlbumState-alakú listát. A tömbmutató írója lezárható; a benne levő `double` érték naptári kódolása, a bemeneti objektum konkrét osztálya és a qshow-listához vezető átalakító út továbbra is nyitott.

**A `+0xbc8+0x58` dátumtömbmutató írója.** A `0x00415790` CThumbDB-konstruktor a másodlagos bázis vtable-jét a teljes objektum `+0x48` mezőjébe írja (`0x00415804`, cél: `0x00c81fa4`). E bázis `+0x20` virtuális helye a `0x0044f7c0` (`0x00c81fc4`), amely a `this+0xbc8` alobjektumra lép (`0x0044f80f`), annak vtable `+0x18` helyét hívja (`0x0044f844`-`0x0044f84b`), majd az alobjektum `+0x58` mutatójából kér indexelt qwordot (`0x0044f857`-`0x0044f871`). A getter `this`-e a teljes CThumbDB-objektum `+0x48` címe, ezért az alobjektum kezdete a teljes objektum `+0xc10`, az olvasott mutató mezője pedig `+0xc68`.

Független konstruktorút köti ugyanezt az alobjektumot a dátumoszlophoz: a `0x00415790` a `"date"` mező-kulcs előkészítése után a teljes objektum `+0xc10` címét adja a `0x00495d30`-nak (`0x00415950`-`0x0041596f`). Ez a konstruktor a `0x00c822d4` vtable-t írja be és a saját `+0x58` mezőjét nullázza (`0x00495d45`-`0x00495d80`). Az RTTI ezt `CColumn<double,1,322043906>`-ként nevezi meg; a vtable `+0x18` slotja a `0x00495d90`.

A `0x00495d90` az üres `+0x54` gyorsítótár esetén meghívja a `0x00499650`-et. Ez a lekérő (`0x006a41e0`, azonosítóargumentuma `0x13320002`) által visszaadott struktúracímhez `0x234`-et ad, az eredeti címet a `+0x54` mezőbe és a kapott `+0x234` mutatót a CColumn `+0x58` mezőjébe írja (`0x00499670`-`0x00499688`). A `0x0044f7c0` getter ugyanezt a `+0x58` mezőt fogyasztja. A pontos író tehát **`0x00499650`**, az adatlekérő hívás **`0x006a41e0`**.

| Állítás | Bizonyíték | Fok |
|---|---|---|
| A dátumgetter a CThumbDB `+0x48` bázis `+0xbc8` alobjektumának `+0x58` mutatójából olvas. | bináris (`0x00415790`, `0x00415804`, `0x0044f7c0`, `0x00c81fc4`) | megerősített: getter és külön konstruktor/vtable út egyezik |
| Az alobjektum a `CColumn<double,1,322043906>` dátumoszlop. | bináris (`0x00415790`, `0x00415950`-`0x0041596f`, `0x00495d30`, RTTI `0x00c822d4`) | megerősített |
| A `+0x58` mutatót a `0x00499650` tölti, a `0x006a41e0` által visszaadott struktúra `+0x234` címére állítva. | bináris (`0x00495d90`, `0x00499650`, `0x006a41e0`) | megerősített: a vtable-fogyasztó és az író külön utasításútja egyezik |
| A visszaadott `double` qwordok pontos naptári epochja, egysége vagy átalakítása. | **NINCS MEG** | nyitott |

A `2026-10-22-idorend-38.txt` meglévő dekompilációja a `0x006a41e0` generikus oszloplekérését írja le, a `0x13320002` azonosítóhoz tartozó dátumformátumot és naptári átalakítást nem. A CColumn típusa igazolja a lebegőpontos tárolást, de abból nem következik epoch vagy képlet; ilyen értéket nem adok meg.

**A qshow-lista és a szűrők.** A `0x006dc4c0` a paraméterként kapott objektum `+0x2c0` értékét adja a `0x004b8ee0`-nak (`0x006dc626`-`0x006dc62c`). A `0x004b8ee0` a `[+0x138]` 0x24 bájtos rekordjai közül a `+0x0c != 0` feltételű rekordok *sorszámát* írja a `+0x148` dword-tömbbe, és a `+0x14c` elemszámot növeli (`0x004b9022`, `0x004b9028`, `0x004b90b4`, `0x004b90c7`). Ez az alak CAlbumState-rekordokkal kompatibilis; a `0x006dc4c0` bemeneti objektumának konkrét RTTI-osztálya ettől még nem bizonyított.

A `0x004b8470` a `+0x148` dword-listát `+0x14c >> 1` elemszámmal olvassa. Ha a `[this+0x9d]` bájt nem nulla, a `0x004461a0` a `[this+0xc4]` objektumot és az aktuális sorszámot kapja; hamis visszatérésnél az elem kimarad (`0x004b85a0`-`0x004b85bf`). A `0x004461a0` helyi utasításolvasata szerint a bemeneti objektum `+0x48` mezőjének vtable `+0x14` slotját hívja meg kimeneti mutatóval, majd a kimenet nulláját és egy `& 0xffffff00 == 0x100` tesztet használ. Ez a gépi feltétel ismert, de a mező és a predikátum tartalmi jelentése **NINCS MEG**.

A `0x004b8470` az EAX-ban kapott sorszámot és egy veremre tett kontextust ad a `0x004b29d0`-nak (`0x004b85c1`-`0x004b85c8`). A kontextus `+0x48` mezője a `0x004b8470` `this`-e, a `+0x4c` mező a `this+0xc4` értéke (`0x004b851b`-`0x004b8523`). A `0x004b29d0` a `[+0x138 + sorszám*0x24 + 0x0c] == 2` feltételt vizsgálja, majd a `0x0044ddd0` útján kér le további dwordot; a rekord mezőinek jelentése **NINCS MEG**. A `0x38` bájtos kimeneti rekord nem lehet a qshow `0xf8` bájtos kártyalistájának ugyanaz a nyers puffer, de köztes átalakítás nincs kizárva.

**A `+0x2c0` mező osztálya: a hasonló eltolás nem típusbizonyíték.** A `0x005de8e0` a CThumbUI vtable egyik metódusa (`0x00c90584`, 22. slot), de `__thiscall` függvény: a saját `this`-e ECX-ben marad. A `0x005dedb3`-`0x005dedbc` utasítások egy külön veremargumentumot és a másik paramétert adják a `0x005d3290`-nak; a Ghidra-kimenet (`2026-10-21-koteg-1021b.txt`) ezt `FUN_005d3290(param_1,param_2)` alakban mutatja. A `0x005d3290` a saját `param_1` értékét adja tovább a `0x006dc4c0`-nak (`2026-10-29-koteg-33.txt`). Ezért nem következik, hogy a `0x006dc4c0` `[param_1+0x2c0]` mezője a `CThumbUI+0x2c0` `CAlbumState` pointer; a vtable-módszer `this`-e nem az átadott első paraméter. A paraméter pontos osztálya **NINCS MEG**.

| Állítás | Bizonyíték | Fok |
|---|---|---|
| A `+0x148/+0x14c` mező dword sorszámlista a `+0x138` 0x24 bájtos rekordtömbhöz. | bináris (`0x004b8ee0`, `0x004b8470`) | megerősített a lista alakjára; a futásidejű bemeneti osztály nyitott |
| A `0x004b29d0` argumentumai: sorszám EAX-ban és a `+0x48/+0x4c` mezőjű stack-kontextus. | bináris (`0x004b8470`, `0x004b29d0`) | megerősített |
| A `[this+0x9d]` predikátum és a rekord `+0x0c == 2` mező értelmezése. | NINCS MEG; a gépi feltétel címei: `0x004461a0`, `0x004b29d0` | nyitott |
| A `0x006dc4c0` bemeneti paraméterének `+0x2c0` mezőtulajdonosa és osztálya. | NINCS MEG; a `0x005de8e0` explicit paramétert ad tovább, nem a saját `this`-ét | nyitott |
| A `0x004b29d0`/`0x0044ddd0` kimenetének azonossága vagy átalakítása a qshow `+0xac` bemenetévé. | NINCS MEG; rekordméretek: `0x38` és `0xf8` | nyitott |

**A két független út.**

- **Qshow-lista:** A út: a `0x004b8ee0` előállítja a sorszámokat a rekordtömbből. B út: a külön `0x004b8470` fogyasztja ugyanazt a listát és a sorszámot a `0x004b29d0`-nak adja; annak `+0x0c == 2` rekordvizsgálata azonos indexelési alapot használ. A két út a lista alakjában egyezik. Egyik sem igazolja a `0x006dc4c0` paraméter RTTI-osztályát vagy a qshow `+0xac` kimeneti kapcsolatot.
- **Dátumoszlop:** A út: a `0x0044f7c0` a CThumbDB másodlagos bázisának `+0xbc8+0x58` mutatóját olvassa, a konstruktorút pedig ugyanarra a teljes objektumbeli `+0xc10` CColumn-példányra mutat. B út: a `CColumn<double>` RTTI-vtable `+0x18` célja `0x00495d90`, amelynek lusta betöltője a `0x00499650` írót hívja. A fogyasztó és az író ugyanahhoz a CColumn `+0x58` mezőhöz vezet.

**Cáfoló kísérlet.** Két kézenfekvő, de hibás azonosságot vizsgáltam. (1) A hét közvetlen `+0xc20` író egyike, a `0x006ba4a0`, nem a dátum-CColumn írója: a CThumbDB konstruktor a külön `+0x3200` alobjektum címét adja neki (`0x00415ed4`-`0x00415f05`), és a `+0xc20` saját címhez képesti mezője nem a CThumbDB `+0xbc8+0x58` út. A `0x00477920` korábbi jelöltje is más `+0x1a48+0x58` tárolót ír. (2) A `CThumbUI+0x2c0` típust nem vetítettem rá a `0x006dc4c0`-ra: a `0x005de8e0` vtable-függvényben ECX a saját `this`, az explicit `param_1` ettől külön kerül a `0x005d3290`-ba. A gépi kód mindkét cáfolatot közvetlenül ellenőrzi.

**Bizonyítottsági fok.** A CColumn dátummutató konkrét írója **megerősített**; a naptári képlet **nyitott**. A listaproducer és -fogyasztó sorszámlistája, valamint a `0x004b29d0` argumentumszerződése a felsorolt bináris utak szerint megerősített. A bemeneti objektum konkrét osztálya, a szűrők jelentése, a qshow-kártyalistával való átalakító kapcsolat és a PicasaPy teljes gyűjteménylistájával való azonosság **nyitott**. E körből új, bizonyított PicasaPy-eltérés nem következik.

**A #6532 „Kész, ha” pontjai.** (1) ✅ Az eredeti videókat a job-373 és job-446 felvétel dokumentálja (38.2.101, 38.2.104). (2) ⛔ Nem minden megvalósítandó részhez van binárisból igazolt forráshalmaz, szűrőjelentés és dátumkódolás. (3) ⛔ A teljes qshow-kártyakészlet és a PicasaPy-lista futásidejű azonosságára nincs tételes összevetés; új fejlesztési eltérés nem bizonyított. (4) ⛔ A #6713 meglévő fejlesztési jegy a korábban igazolt eltérésekre hivatkozik, de ebben a körben nem készült kiadásba adható összehasonlító videó vagy képsor.

**Nyitott.**

- Ghidra-kör kell: 0x005de8e0 - a CThumbUI vtable-módszer explicit `param_1` argumentumának forrása és osztálya; a meglévő `2026-10-21-koteg-1021b.txt` csak a `0x005d3290`-nak történő továbbadást mutatja, nem az argumentum típusát. A `0x006dc4c0` `+0x2c0` mezőjének tulajdonosa e nélkül nem dönthető el. [blokkoló]
- Ghidra-kör kell: 0x004461a0 - a `+0x48` alobjektum `+0x14` virtuális helyének típusa és a kimeneti zászló tartalmi jelentése; a helyi diszasszembly csak a gépi null-/bitfeltételt adja meg. [blokkoló]
- Ghidra-kör kell: 0x0044ddd0 - a `0x004b29d0` által kért dword pontos rekordforrása és van-e átalakító kapcsolat a qshow `+0xac` bemenetéhez; a helyi utasításolvasat a `+0x988/+0xc78` mezőutakat mutatja, de nem nevezi meg a descriptor szemantikáját. [blokkoló]
- Ghidra-kör kell: 0x006a41e0 - a `0x13320002` `date` adatlekérésének numerikus naptári kódolása és a visszaadott `+0x234` qword-sor jelentése; a meglévő `2026-10-22-idorend-38.txt` generikus oszlop-cache viselkedést mutat, nem a dátum átalakítását. [blokkoló]
- A qshow bemeneti rekordok teljes forráshalmaza, az album/mappa/csoport kategóriák azonossága és a PicasaPy-gyűjteményekkel való futásidejű egyezés **NINCS MEG**. A megszerzéshez az előző három Ghidra-kérdés után az azonos eredeti Picasa-futás descriptor-azonosítóit és kártyáit kell mérni.

**Új kutatási jegyjavaslat.** Nincs; ezek a nyitott pontok a #6532 „Kész, ha” feltételeihez tartoznak.

**Módosított fájlok ebben a szakaszban.** Ez a 38.2.107 a helyi bináris/Ghidra-bizonyítékot dokumentálja; kódot, tesztet, eredeti binárist vagy mérőadatot nem módosítottam.

#### 38.2.108 A qshow bemeneti osztálya, szűrője és dátumkódolása (#6532, 2026-11-11)

**Hatókör és módszer.** A 2026-11-11-i Colab Ghidra-kimeneteket az eredeti `Picasa3.exe` utasításszintű olvasatával ellenőriztem. A qshow-hidat a korábbi `38.2.63` és `38.2.69` adatútjaival, a `0x004461a0` predikátumot pedig a `picasa-keptalca.md` 20.3 szakaszának két független felhasználásával kereszteztem. A dátumkódolásnál a gettert, a dekódolót, a kódolót és azok konstansait vizsgáltam. Új Wine-mérés és PicasaPy-futásidejű összevetés nem készült.

**A 38.2.107 osztályra vonatkozó állításának javítása.** A `0x006dc4c0` bemeneti objektuma a `CThumbUI`, nem egy ismeretlen osztályú, `+0x2c0` mezővel bíró külön objektum. A `0x005de8e0` a `CThumbUI` vtable `0x00c90584` slotja (`0x00c9052c` vtable). A metódus a belépő `ECX` értékét `0x005de8f6`-nál elmenti; a `0x005dedb3`-`0x005dedbc` helyen az eseményargumentum mellett ezt az elmentett `this` pointert is átadja a `0x005d3290`-nak. A `0x005d3290` ugyanezt az első paramétert továbbadja a `0x006dc4c0`-nak. A `0x006dc4c0` a `CThumbUI+0x2c0` mezőt adja a `0x004b8ee0`-nak. A `38.2.69` független konstruktor- és RTTI-útja ezt a mezőt `CAlbumState`-ként azonosítja.

**A qshow-híd közvetlen.** A `0x005e96d9` a `CThumbUI+0x2c0` pointert a MakeTimeline paraméterrekord `+0x14` mezőjébe teszi. A `0x007fa7f0` ezt változtatás nélkül másolja a oneup `+0x2f4` mezőjébe, majd a `0x007fb9f0` a pointert a qshow `+0xac` mezőjébe írja (`0x007fb9f0`, `mov [esi+0xac], ecx`). A qshow kártyaépítője, `0x007fc7c0`, ebből a CAlbumState pointerből olvas. A `0x004b8ee0`/`0x004b8470` út ugyanezen CAlbumState lista- és rekordmezőit dolgozza fel. A különböző rekordméretű köztes adatok a qshow saját kártyarekordjaivá alakulnak, de a CAlbumState pointer előtt nincs külön adapter. Ez lezárja a pointerhíd kérdését, nem nevezi meg a CAlbumState teljes forráshalmazát.

**A `+0x9d` szűrő gépi hatása.** A `0x005db823` a `thumbui/soloview` és `thumbui/folderview` kulcsok értékét a `0x004a7300` setternek adja; a setter az elsőt a CAlbumState `+0x9c`, a másodikat a `+0x9d` mezőbe írja. A `0x004b8470` nem nulla `+0x9d` esetén a `0x004461a0` predikátumot hívja, hamis visszatérés esetén kihagyja az adott sort. A `picasa-keptalca.md` 20.3 a predikátum két másik felhasználásából igazolja, hogy nem nulla eredménye albumot, nulla eredménye mappát jelent. Így ezen az útvonalon a nem nulla `+0x9d` az albumként besorolt sort tartja meg. A beállítás felhasználói jelentését nem vezetem le pusztán a kulcs nevéből.

**A rekord `+0x0c` mezőjének határa.** A `0x004b29d0` a `CAlbumState+0x138 + index*0x24 + 0x0c` értéket `2`-vel hasonlítja össze; az elfogadott ágon a `0x0044ddd0` további adatot kér. A bináris tehát igazolja, hogy a `2` egy elfogadott rekordállapot a qshow felé vezető listában. A tartalmi címke, például hogy albumot vagy más gyűjteményfajtát jelöl-e, **NINCS MEG**. A `0x004ba420` a rekord mezőit másolja, de az értéket nem állítja elő. A már vizsgált `0x004a66e0`, `0x004abe70` és `0x004a57a0` sem adott bizonyított írócímet vagy enumnevet.

**A dátum-qword kódolása.** A `0x0044f7c0` a CThumbDB dátumoszlopának `double` qwordját olvassa; a lusta oszlopbetöltő `0x00499650` a `0x006a41e0` `0x13320002` lekérésének eredményéből tölti a tárolót (lásd `38.2.107`). A qshow `0x007fc4c0` útja a `0x0098ba30` és `0x0098b9e0` átalakítókon, majd a `0x0098b550` kódolón halad át; a dátumot dekódoló segéd a `0x0098b320`. A kódoló 86400 másodperccel számolja a nap törtrészét (`0x00cf3f20`), és a dátumnapokból kivonja a 693959-es alapot (`0x000a96c7`). A bináris naptári napösszeg-képlet szerint ez 1899-12-30 napja: `1899*365 + 460 + 334 + 30 = 693959`. A `0x0098b320` ugyanazt a nap/törtrész felbontást és a Gergely-naptári 400/100/4 éves ciklusokat használja. A qword tehát Gergely-naptári napok sorszáma 1899-12-30 kezdőnappal, a törtrész pedig a napon belüli idő. A dekódoló tartományhatárai `-657434` és `2958465` (`0x00cf3f38`, `0x00cf3f40`).

**A képszolgáltató slotja.** A qshow `[this+0x2e4]` virtuális `+8` célja `0x00424b10`. A `CThumbDB+0x4c` beágyazott felületének vtable-je `0x00c820a8`; a konstruktor- és vtable-adatút ezt köti a szolgáltatóhoz. A hívás a kártyarekordot és a kért méretet adja át. A forrásméret-lépcső és a 640 px-es küszöb részletes bizonyítéka a `38.2.97` szakaszban van; az új Ghidra-kör nem talált eltérést.

| Állítás | Forrás |
|---|---|
| A `0x006dc4c0` bemeneti objektuma CThumbUI, `+0x2c0` mezője CAlbumState. | bináris (`0x005de8e0`, `0x005d3290`, `0x006dc4c0`, `0x004a1560`, vtable `0x00c9052c`, RTTI `0x00c8368c`) |
| A qshow `+0xac` ugyanazt a CAlbumState pointert kapja; a qshow utána maga építi kártyarekordjait. | bináris (`0x005e96d9`, `0x007fa7f0`, `0x007fb9f0`, `0x007fc7c0`) |
| Nem nulla `+0x9d` mellett az albumként besorolt sort megtartja a predikátum. | bináris (`0x005db823`, `0x004a7300`, `0x004b8470`, `0x004461a0`; a predikátum jelentésének külön ellenőrzése: `0x00537fb0`) |
| A rekord `+0x0c == 2` jelentése az elfogadott státuszon túl. | NINCS MEG |
| A dátum `double` kezdőnapja, egysége és törtrészének szerepe. | bináris (`0x0044f7c0`, `0x00499650`, `0x0098b320`, `0x0098b550`, `0x00cf3f20`, `0x00cf3f38`, `0x00cf3f40`, `0x000a96c7`) |
| A `[this+0x2e4]` képszolgáltató virtuális `+8` célja. | bináris (`0x00802230`, `0x00415790`, `0x00424b10`, vtable `0x00c820a8`; részletek: `38.2.97`) |
| A qshow teljes futásidejű forráshalmaza és annak azonossága a PicasaPy Időrend-listájával. | NINCS MEG |

**A két független út.** A út: a `0x005de8e0` mentett `this` pointerét a hívási utasítások a `0x005d3290`-on keresztül a `0x006dc4c0`-ig viszik; a qshow paraméterrekord útja ugyanezen `CThumbUI+0x2c0` pointert adja a qshow `+0xac` mezőjének. B út: a `CThumbUI` vtable RTTI-azonosítása és a `0x004a1560` konstruktor `CAlbumState` vtable-írása külön típustámpontot ad, összhangban a `38.2.69` korábbi típusbizonyításával. A két út egyezik a bemeneti osztályban és a pointerben.

A dátumnál A út a getter és a dekódolók útja, amely a qwordot napra és napon belüli törtrészre bontja. B út a kódoló külön naptári mezőkből képzett napösszege, amelyből kivonja a 693959 alapot és 86400-zal osztja az időt. A két irány ugyanazt az epochot és egységet adja. A `0x004461a0` jelentését két külön UI-felhasználás, az albumkijelölés és a mappa kijelölése ellenőrzi (`picasa-keptalca.md` 20.3).

**Cáfoló kísérlet.** Megpróbáltam megtartani a 38.2.107 korábbi olvasatát, miszerint a CThumbUI virtuális metódusának `this` pointere nem jut el a `0x006dc4c0`-ig. A `0x005de8e0` mentett ECX-értékét közvetlenül a `0x005d3290` első argumentumába, onnan pedig a `0x006dc4c0` első argumentumába követtem; ez cáfolja a korábbi olvasatot. Külön próbáltam a qwordot Unix-másodpercnek tekinteni: a naptári dekódoló és kódoló közös 86400-as osztója, 693959-es kezdőnapja és Gergely-naptári ciklusai ezt cáfolják. A rekord `+0x0c` tartalmi értelmezését nem próbáltam azonosítani puszta mezőnévből vagy hasonló rekordból.

**Bizonyítottsági fok.** A bemeneti CThumbUI/CAlbumState osztályazonosság, a qshow pointerhíd, a `+0x9d` album-predikátumának hatása, a dátum-qword kódolása és a képszolgáltató `0x00424b10` célja **megerősített**, mert két független bináris vagy bináris és RTTI/UI út egyezik. A `+0x0c == 2` rekordállapot tartalmi neve, a teljes qshow forráshalmaz és annak PicasaPy-listával való azonossága **nyitott**. E körben új PicasaPy-viselkedési eltérés nem igazolódott.

**A #6532 „Kész, ha” pontjai.** (1) ✅ Az eredeti videó dokumentált: job-373 és job-446 (`38.2.101`, `38.2.104`); a billentyű-leütések pontos képkockakapcsolata továbbra is nyitott. (2) ⛔ A teljes forráshalmaz, a `+0x0c == 2` szemantikai címkéje, a PicasaPy-listával való azonosság és a billentyű-képkocka szinkron még nem igazolt. (3) ✅ A felhasználó által átadott jegyelőzmény megvalósítási jegyként nevezi meg a #6713-at; a GitHub-állapotot nem ellenőriztem. (4) ⛔ Kiadásba adható PicasaPy-összehasonlító videó vagy képsor nincs dokumentálva.

**Következő konkrét vizsgálat és nyitott pontok.** A `+0x0c` jelentéséhez előbb a CAlbumState `+0x138` 0x24 bájtos rekordjainak mezőíróját kell utasításszinten megtalálni. A következő helyi célpontok a `0x004a66e0` rekordpuffer-kezelése és hívásai, majd a `0x004abe70` és `0x004a57a0` feltöltő út; a `0x004ba420` már vizsgált rekordmásoló, nem értékíró. Csak a konkrét mezőíró azonosítása után érdemes annak pontos címére új Ghidra-kört kérni. A teljes forráshalmazhoz a `0x004b8ee0` → `0x004b8470` → `0x004b29d0` szűrőút minden bemeneti ága és a `0x007fc7c0` kártyaépítő futásidejű listája szükséges; enélkül PicasaPy-eltérés nem állítható.

**Nyitott.**

- A rekord `+0x0c == 2` tartalmi jelentése **NINCS MEG**. Következő út: mezőíró keresése a `0x004a66e0`, `0x004abe70`, `0x004a57a0` feltöltési ágai mentén; utána az azonosított konkrét író célzott Ghidra-dekompilációja.
- A teljes qshow-bemeneti gyűjteményhalmaz és a PicasaPy-listával való futásidejű egyezés **NINCS MEG**. Következő út: a `0x004b8ee0`, `0x004b8470`, `0x004b29d0` szűréseinek teljes adatútja, majd ugyanazon futásból gyűjtött descriptorok és kártyák összevetése a PicasaPy listájával.
- A billentyű-események és az első/utolsó mozgó képkocka pontos kapcsolata, valamint a tényleges Wine Preferences-értékek **NINCS MEG** (`38.2.104`). Megszerzéséhez képkockára szinkronizált eseménynapló és azonos futásból mentett beállítások szükségesek.

**Új kutatási jegyjavaslat.** Nincs; a nyitott pontok a #6532 meglévő elfogadási feltételei.

**Módosított fájlok ebben a szakaszban.** Ez a 38.2.108 a 2026-11-11-i Ghidra-kimenetekkel és a helyi bináris ellenőrzéssel javítja a 38.2.107 osztályolvasatát, valamint lezárja a dátumkódolást és a qshow-hidat. Kódot, tesztet, videót, eredeti binárist vagy mérőadatot nem módosítottam.

#### 38.2.109 A CAlbumState forrásút szűrői és a PicasaPy dátumkulcsa (#6532, 2026-11-11)

**Hatókör és módszer.** A 2026-11-11-i Colab Ghidra-kimeneteket a `0x004a66e0`, `0x004abe70`, `0x004a57a0`, `0x004ba420`, `0x004b8ee0`, `0x004b8470`, `0x004b29d0` és `0x007fc7c0` címeknél olvastam. A forráslistát, a qshow-szűrőket és a dátummezőt célzott `annot_disasm.py` olvasattal, az osztálymezőt pedig RTTI-alapú `offset_map.py` leltárral ellenőriztem. A teljes `.text` eltoláskeresés első művelete `paszta.memoria_kapu()` volt. A PicasaPy összevetés a `timeline_controller.py` és a `TimelineView.qml` aktuális forrását követi. Új Picasa/Wine-felvétel nem készült.

**A bemeneti descriptorok felépítése.** A `0x004a66e0` a CAlbumState `+0x138` mutatójú, `+0x13c` számlálójú, `0x24` bájtos rekordsorozatának kapacitását kezeli. A meglévő sorokat a `0x004ba420` másolja. A `0x004a66e0` `FastStart == 0` esetben a `0x004abe70` és a `0x004a57a0` feltöltő útvonalat hívja. A `0x004abe70` szövegei között szerepel a `Folders on Disk`, `My Albums`, `Exported Pictures`, `Other Stuff`, `Labels`, `People`, továbbá feltételes `Outlook` és `Hello Albums~`. A `Starred Photos`, `Screensaver`, `Recently Updated`, `Emailed` és `Uploaded` ágak is szerepelnek. Ezek az építőútban megjelenő nevek és belső kulcsok, nem bizonyítják, hogy mindegyikből látható Időrend-kártya lesz. A `0x004a57a0` CThumbDB-elemek több `+0x18` típusértékét és további jelzőit szűri; ezek a típusok nincsenek a látott forrásban gyűjteménynévhez kötve.

**A lista és a qshow-szűrők.** A `0x004b8ee0` végigmegy a `+0x138` rekordokon. A `+0x0c != 0` rekord indexét a `+0x148` sorszámlistához adja, ha a lista `+0x14c` jelzőjének bit 0 értéke nulla; minden ilyen rekordnál a `0x004b86d0` is lefut. A `0x004baaa0` rendezi a sorszámlistát, majd a `0x004b8470` felépíti a `+0x158/+0x15c` 0x38 bájtos köztes listát.

A `0x004b8470` a `[this+0x9d] == 0` esetben közvetlenül meghívja a `0x004b29d0`-t. Nem nulla `+0x9d` esetén csak az az index jut tovább, amelyre a `0x004461a0` igazat ad. Ennek a predikátumnak a külön, `picasa-keptalca.md` 20.3 szakaszában igazolt jelentése szerint az igaz albumot, a hamis mappát jelöl. A `0x004b29d0` a `CAlbumState+0x138 + index*0x24 + 0x0c` értékét `2`-vel hasonlítja össze; ha nem egyezik, nem tesz 0x38 bájtos rekordot a köztes listába. A mező írója `0x004ab520`; a `2` tartalmi neve továbbra is **NINCS MEG** (38.2.110).

A qshow `0x007fc7c0` a `+0x158/+0x15c` listát olvassa, és csak a 0x38 bájtos rekord `+0x30 == 1` és `+0x18 == 0` feltételű elemeinek sorszámát tartja meg. A megtartott sorokhoz a CThumbDB adatútján kér adatot, és felépíti a saját 0xf8 bájtos kártyarekordjait. Ez összeköti a listaépítést a qshow-val, de a köztes numerikus mezők nem nevezik meg a forrásul szolgáló gyűjteményfajtát.

**PicasaPy összevetés.** A `TimelineController._do_reload()` a látható indexelt fotókból mappák szerint gyűjt, majd az ismert albumok közül a nem üreseket adja hozzá (`src/picasapy/app/timeline_controller.py:218-239,269-291`). Az album- és mappakártya dátuma a legkorábbi tag EXIF-dátum (`:357-382`). A dátumot a `datetime.fromisoformat(...).date()` napra csonkolja, majd a sorrend azonos napnál név és azonosító szerint dönt (`:293-299`). A nap-szintű `sliderPosition` a `date.toordinal()` értékek különbségéből készül (`:301-320`); a `TimelineView.qml` ezt a normalizált értéket használja (`:73-79`).

Az eredeti qshow dátumkulcsa `double`: a `0x0098b550` a naptári napösszegből levonja a `0x000a96c7` értéket, és a másodpercet a `0x00cf3f20` 86400-as osztójával a nap törtrészévé alakítja. A dekódoló `0x0098b320` ezt a napot és törtrészt visszabontja. A kezdőnap `1899-12-30`, a törtrész tehát napszakot is őriz (részletes kétirányú bizonyíték: 38.2.108). A qshow ezt a teljes dátum-qwordot növekvő sorrendben használja (`0x007fc4c0`, `0x0049cd60`). Ez a rendezés dátumkulcsra vonatkozó bizonyíték, nem a kártyák pályán elfoglalt pozíciójának képlete.

**Eredeti / nálunk / teendő.**

| Eredeti Picasa | Jelenlegi PicasaPy | Teendő |
|---|---|---|
| A qshow kártyák sorrendje a dátum-qword szerint növekvő; a qword nap-törtrésze időt is kódol (`0x007fc4c0`, `0x0049cd60`, `0x0098b550`). A CAlbumState teljes kártyaforrása és a `+0x0c == 2` kategóriája **NINCS MEG**. | Csak mappa- és nem üres albumkártyák készülnek. A dátum napra csonkolt, a gyűjtemények sorrendje dátum, név, azonosító (`timeline_controller.py:269-299,357-382`). | A PicasaPy dátumkulcsa őrizze meg a napszakot, és azonos naptári nap esetén a teljes időponttal rendezzen. A forrásokból még nem igazolt, hogy egy eredeti descriptor dátumkulcsa pontosan a PicasaPy által számított legkorábbi EXIF-időpontnak felel meg, ezért a felhasználói sorrendkülönbség erre az egyező adatra feltételes. A gyűjteményfajták egyeztetése csak a CAlbumState mező jelentésének feloldása után zárható le. |

**Bizonyíték.**

| Állítás | Forrás |
|---|---|
| A CAlbumState `+0x138/+0x13c` rekordpuffere `0x24` bájtos sorokkal működik; `0x004ba420` másolja a mezőket. | bináris (`0x004a66e0`, `0x004ba420`) |
| A `0x004b8ee0` a nem nulla `+0x0c` rekordok sorszámát gyűjti, a `0x004b8470` alkalmazza a `+0x9d` útvonalat. | bináris (`0x004b8ee0`, `0x004b8470`, `0x004461a0`) |
| A `+0x0c == 2` a `0x004b29d0` szükséges feltétele a köztes rekord létrehozásához. | bináris (`0x004b29d0`) |
| A qshow kártyaépítő további `+0x30 == 1` és `+0x18 == 0` feltételt vizsgál. | bináris (`0x007fc7c0`, `0x004ae4e0`) |
| A dátum-qword napszakot kódoló törtrészt és `1899-12-30` kezdőnapot használ. | bináris (`0x0044f7c0`, `0x0098b320`, `0x0098b550`, `0x00cf3f20`, `0x000a96c7`) |
| A qshow dátumkulcs szerinti iránya növekvő. | bináris (`0x007fc4c0`, `0x0049cd60`) |
| A PicasaPy `taken_at` értékét naptári napra csonkolja, a gyűjteményt a legkorábbi tagdátummal, majd dátum, név és azonosító szerint rendezi. | PicasaPy-forráskód (`src/picasapy/app/timeline_controller.py:293-299,357-382`) |
| A +0x138 rekordok +0x0c mezőjének írója `0x004ab520`; a `2` kód tartalmi neve. | bináris (`0x004ab520`); a név **NINCS MEG** |
| A qshow-ban ténylegesen megjelenő összes gyűjteményfajta. | NINCS MEG |

**A két független út.**

- **A út, eredeti bináris.** A `0x004b8ee0` a CAlbumState listából sorszámokat gyűjt; a `0x004b8470` ebből tölti a `+0x158/+0x15c` köztes listát; a `0x007fc7c0` ugyanennek a CAlbumState objektumnak a listáját használja a kártyaépítéshez. A korábban lezárt `0x005e96d9` → `0x007fa7f0` → `0x007fb9f0` pointerút külön igazolja, hogy a qshow ezt a CAlbumState pointert kapja (`38.2.108`). A forrásneveknél a `0x004abe70` hívásai és a hozzájuk tartozó bináris karakterláncok egyeznek.
- **B út, PicasaPy forráskód.** A controller kifejezetten mappa- és albumgyűjteményeket készít, `.date()`-tal elveszíti a napszakot, és azonos napnál névvel rendez. A QML a normalizált `sliderPosition` mezőt használja. Ez független implementációs rétegként megerősíti a kódok közötti dátumfelbontás-eltérést, de nem igazolja, hogy a teljes eredeti descriptorlista azonos az app kártyahalmazával.
- **Egyezés.** Az eredeti dátum-qword napszakot is tárol, a PicasaPy pedig az `taken_at` értéket napra csonkolja; ez a két implementáció összevetésében megerősített felbontásbeli eltérés. Látható sorrendi hatása akkor áll elő, ha a megfelelő gyűjteménydátumok ugyanarra a naptári napra esnek, de eltér az időpontjuk. Azt, hogy az eredeti descriptor dátuma ugyanazt az adatot jelenti-e, mint a PicasaPy legkorábbi EXIF-dátuma, még nem igazoltuk. A teljes halmaz azonossága nyitott.

**Cáfoló kísérlet.** Megpróbáltam cáfolni azt a feltételezést, hogy a `+0x0c != 0` önmagában azt jelenti, hogy a sor kártyaként megjelenik. A `0x004b29d0` külön `== 2` feltételt alkalmaz, majd a `0x007fc7c0` még két további rekordmezőt vizsgál; ezért a nem nulla értékből nem következik kártyatagság. A cáfoló út ugyanazon mércével ellenőrizve közvetlen gépi feltételeken alapul, nem index-negatív találaton. Azt is próbáltam cáfolni, hogy a Python ordinal epoch önmagában eltolná a PicasaPy normalizált csúszkáját: a `sliderPosition` képlet mindkét végpontból levonja az első ordinalértéket, így az állandó epocheltolás kiesik. A maradó eltérés a napszak eldobása.

**Bizonyítottsági fok.** A `+0x0c != 0`, `+0x0c == 2`, `+0x9d` és a qshow végső mezőszűrői gépi feltétele **megerősített**. A PicasaPy kódjának napra csonkolása és az eredeti qword törtrészének megőrzése közötti implementációs eltérés **megerősített**; tényleges, felhasználó által látható sorrendváltás csak azonos napi, eltérő időkulcsú gyűjteménynél következik, futásidejű mintakészlet még nincs. A qshow teljes forráshalmaza és a `+0x0c == 2` mező neve **nyitott**. Az összes kérdésre vonatkozó bizonyítottság ezért **feltételes**.

**A #6532 „Kész, ha” pontjai.** (1) ✅ A korábbi eredeti felvételek a 38.2.101 és 38.2.104 szakaszban vannak dokumentálva; új felvétel ebben a körben nem készült. (2) ⛔ A qshow végső feltételei és a CAlbumState-építőút bővült, de a `+0x0c` mező írója, a `2` kategóriája és a teljes kártyaforrás nyitott. (3) ⛔ A PicasaPy napra csonkolási eltérése azonosított, de a teljes forráshalmazzal való tételes összevetés nem zárult le. (4) ⛔ A korábban nevezett #6713 nem fedi le bizonyítottan ezt az időbélyeg-eltérést; ehhez fejlesztési jegyszöveg javasolható, de GitHub-művelet és kiadási összehasonlító videó vagy képsor nincs ebben a munkamenetben.

**Javasolt jegytörzs-bővítés.**

> Javasolt cím: Időrend: őrizze meg a gyűjtemény dátumkulcsának napszakát. Eredeti: a qshow a dátum-qword teljes értékével rendez (`0x007fc4c0`, `0x0049cd60`); a qword nap-törtrésze napszakot is tartalmaz (`0x0098b550`). Nálunk: a `src/picasapy/app/timeline_controller.py:357-382` az EXIF-időpontot naptári napra csonkolja, majd a `:293-299` azonos napnál név és gyűjteményazonosító szerint rendez. Teendő: a `_exif_date()` és a gyűjtemény `date` mezője őrizze meg az időpontot, a rendezés használja a teljes értéket. Az eredeti descriptor dátumának PicasaPy legkorábbi EXIF-dátumával való azonosságát külön kell igazolni, mielőtt a dátumforrás megfelelőségét állítjuk.
>
> Kész, ha a gyűjtemény dátumkulcsa megőrzi az időpontot, az azonos naptári napra eső, eltérő időpontú megfelelő rekordok sorrendje a teljes kulcs szerint alakul, és a tesztadat összeköti a PicasaPy dátumforrását az eredeti descriptor dátumával. A dátumvonal pozícióképlete külön bináris igazolást igényel. A pontos qshow forráshalmazt ettől külön, a `+0x0c == 2` jelentésének feloldása után kell egyeztetni.

**Új kutatási jegyjavaslatok.** Nincs külön kutatási jegy; a mezőíró és a kategóriatagság a #6532 meglévő nyitott kérdése.

**Nyitott.**

- A `0x004ab520` mezőíró megvan. A `2` tartalmi nevének és a `0x004aa9f0` állapotváltó hívási út jelentésének feloldásához: `Ghidra-kör kell: 0x004aa9f0 - a CAlbumState +0x0c állapotkódjainak jelentése, különösen mitől és milyen gyűjteményeknél lesz az érték 2 [blokkoló]`. A `2026-11-11-6532-colab-138-0c-irok.txt` tartalmazza a `0x004ab520` dekompilációját, de nem a `0x004aa9f0` törzsét.
- `Ghidra-kör kell: 0x004b1a90 - a CAlbumState +0x158 tömbjébe tett 0x38 bájtos rekordok +0x30 és +0x18 mezőinek forrása és jelentése, valamint hogy a +0x30 == 1 mely gyűjteménytípushoz tartozik [blokkoló]`. A `0x007fc7c0` és `0x004ae4e0` meglévő dekompilációi a másolást és numerikus szűrést mutatják, típusnevet nem.
- A `0x004abe70` által épített speciális kategóriák közül melyek élik túl a fenti szűrőket, és az eredeti futásban milyen névvel jelennek meg: **NINCS MEG**. A megszerzéshez a mezőíró és a `2` jelentésének fenti feloldása, majd azonos futású descriptor- és kártyalista kell.
- A teljes mappák, albumok és virtuális gyűjtemények qshow-kártyahalmazának összevetése a PicasaPy-val: **NINCS MEG**. A megszerzéshez ugyanazon könyvtárból kinyert eredeti descriptorlistát a PicasaPy `TimelineController._collections_to_qml()` kimenetével kell összevetni.
- A PicasaPy dátumkulcs tényleges felhasználói eltérése azonos napra eső rekordokkal: **NINCS MEG** mérés. A megszerzéshez az eredeti qword kulcsok és a PicasaPy kártyasorrend egy azonos, időpontot is tartalmazó mintakészletre történő felvétele szükséges.

**Módosított fájlok ebben a szakaszban.** A 38.2.109 bővíti a qshow upstream szűrőútját, a PicasaPy dátumkezelési összevetését és a lezáratlan kérdéseket. Kódot, tesztet, eredeti binárist, videót vagy mérőadatot nem módosítottam.

Ghidra-források (Colab, Ghidra 12.1.2): `referencia/ghidra/2026-11-10-6532-colab-decomp`, `referencia/ghidra/2026-11-10-6532-colab-bc8-58-irok`, `referencia/ghidra/2026-11-11-6532-colab-decomp-2`, `referencia/ghidra/2026-11-11-6532-colab-decomp-3` (picasapy-agent). Fejlesztési jegy ebből a körből: #6807.

#### 38.2.110 A CAlbumState állapotírója és a qshow rekordkapui (#6532, 2026-11-11)

**Hatókör és módszer.** A már meglévő Colab Ghidra-kimeneteket ellenőriztem: `2026-11-11-6532-colab-138-0c-irok.txt`, `2026-11-11-6532-colab-decomp-3.txt` és `2026-11-10-6532-colab-decomp.txt`. Az eredeti `Picasa3.exe` érintett függvényeit külön `annot_disasm.py` diszasszemblálás ellenőrizte. A kódösszevetés a `src/picasapy/app/timeline_controller.py` forrását követte. Új Ghidra-dekompilálás, futó Picasa-mérés és videófelvétel nem történt.

**A CAlbumState +0x0c mező írója.** A `0x004ab520` a harmadik argumentumot közvetlenül a `param_1+0x138 + param_2*0x24 + 0x0c` címre írja (`0x004ab57d`). A Ghidra dekompiláció és az eredeti binárisból olvasott utasítássor ezt egyezően mutatja. A `0x004a8bb0` ugyanerről a mezőről olvas: `1` értéknél `3`-at, `2` értéknél `4`-et ad át az írónak. A `0x004a8bf0` a `3` értéket `1`-re, a `4` értéket `2`-re váltja. A `0x004aa9f0` hívja mindkét állapotváltót, és a mező üres állapotánál `1`-et is ír. Ez a mezőt többállapotú kódként azonosítja, nem gyűjteménytípusként.

**Mit jelent a 2.** A `0x004b29d0` ugyanazon CAlbumState sor `+0x0c` mezőjét `2`-vel hasonlítja össze, és csak egyezéskor építi tovább a 0x38 bájtos köztes rekordot. Így a `2` bizonyítottan a qshow forráslistájába jutás egyik szükséges állapotkódja. A kód tartalmi neve, illetve az, hogy ez milyen felhasználói művelet vagy gyűjteményállapot következménye, **NINCS MEG**. Az albumot és a mappát a `0x004b8470` külön, a `+0x9d` kapcsoló alatt a `0x004461a0` predikátumával választja szét. A két mező útja ezért nem vonható össze.

**A qshow 0x38 bájtos rekordkapui.** A `0x007fc7c0` a `0x004ae4e0` getterrel olvas rekordot a bemeneti objektum `+0x158` tömbjéből. A kimeneti rekord bázisa a `local_13c`; a qshow `local_10c` változója a rekord `+0x30` dwordja, a `local_124` változó pedig a `+0x18` bájtja. A qshow csak akkor vesz fel sorszámot, ha `+0x30 == 1` és `+0x18 == 0`. A getter a mezőket a `0x004ae600` másolóval tölti. A `0x006dc4c0` egy másik, ugyanazt a gettert használó hívó a `+0x30` mező `5`, `6`, `7` értékeit is külön ágban ellenőrzi, majd egy másik feltételben az `1`, `5`, `6`, `7` kódokat fogadja el. Ez a mezőt számszerű osztályozóként támasztja alá. A `1` gyűjteménytípusa és a `+0x18` bájt jelentése **NINCS MEG**.

**PicasaPy összevetés.** A `_do_reload()` rejtett fotók nélkül olvassa az indexelt képeket; az `_collections_to_qml()` mappánként készít kártyát, majd csak a nem üres albumokat adja hozzá (`timeline_controller.py:218-291`). Ebben az útban nincs más gyűjteménytípus. A Picasa eredeti kódja egy állapotkódot (`+0x0c == 2`) és két köztes rekordfeltételt (`+0x30 == 1`, `+0x18 == 0`) bizonyít, de ezek nincsenek mappa, album vagy más gyűjtemény nevéhez kötve. Ezért a PicasaPy listájával való tényleges típuseltérés ebből a körből **nem igazolódott**.

**Eredeti / nálunk / teendő.**

| Eredeti Picasa | Jelenlegi PicasaPy | Teendő |
|---|---|---|
| A forrásba csak olyan CAlbumState rekord kerül tovább, amelynél `+0x0c == 2`; a qshow köztes rekordján további `+0x30 == 1` és `+0x18 == 0` kapu van (`0x004b29d0`, `0x007fc7c0`). A numerikus mezők emberi jelentése nincs meg. | Mappák és nem üres albumok készülnek. Egyéb gyűjteménytípus nincs hozzáadva (`timeline_controller.py:269-291`). | A típusok közti eltérésről nem adható fejlesztői teendő addig, amíg a bináris kódok neve és a tényleges forráslista nem bizonyított. A mezőjelentéshez a célzott Ghidra-kör kell. |

**Bizonyíték.**

| Állítás | Forrás |
|---|---|
| A +0x138 rekordok +0x0c mezőjét `param_3` argumentummal írja a `0x004ab520`, 0x24 bájtos lépésközzel. | bináris (`0x004ab520`, `0x004ab57d`); `2026-11-11-6532-colab-138-0c-irok.txt` |
| A `0x004a8bb0` és `0x004a8bf0` a mező `1/2/3/4` értékei között vált; a `0x004b29d0` a `2`-t követeli meg a rekord továbbépítéséhez. | bináris (`0x004a8bb0`, `0x004a8bf0`, `0x004b29d0`); `2026-11-10-6532-colab-decomp.txt` |
| A qshow köztes rekord `+0x30 == 1` és `+0x18 == 0` feltételét használja. | bináris (`0x007fc7c0`, `0x004ae4e0`, `0x004ae600`); `2026-11-11-6532-colab-decomp-3.txt`, `2026-11-10-6532-colab-decomp.txt` |
| Másik hívó azonos getterből a `+0x30` `5`, `6`, `7` kódjait is olvassa. | bináris (`0x006dc4c0`, `0x004ae4e0`); `2026-11-11-6532-colab-138-0c-irok.txt` |
| A `0x004b8470` album/mappa predikátumát külön `+0x9d` kapcsolóval vizsgálja. | bináris (`0x004b8470`, `0x004461a0`); `2026-11-10-6532-colab-decomp.txt` |
| A PicasaPy Időrendje mappa- és nem üres albumkártyákat készít. | PicasaPy-forráskód (`src/picasapy/app/timeline_controller.py:218-291`) |
| A `+0x0c == 2` állapot felhasználói neve, a qshow `+0x30 == 1` kódjának gyűjteménytípusa és a `+0x18` mező neve. | NINCS MEG |
| Bizonyított kategóriakülönbség az eredeti qshow és a PicasaPy között. | NINCS MEG |

**A két független út.**

- **A út, CAlbumState állapotmező.** A `0x004ab520` utasításszintű írása rögzíti a mezőcímet és a setter argumentumát. Ettől külön a `0x004a8bb0` és `0x004a8bf0` ugyanazt az indexelt mezőt olvassa, majd külön értékekkel hívja az írót; a `0x004b29d0` független fogyasztóként ugyanazon offseten `2`-t vizsgál. Ezek egyeznek abban, hogy a mező állapotkód, és a 2 szükséges a qshow rekordútjához. A tartalmi név egyik útból sem következik.
- **B út, qshow mezők.** A `0x007fc7c0` egyenlőségei az `1` és `0` értéket közvetlenül a kártyalistába jutás kapujává teszik. A külön `0x006dc4c0` ugyanazon getterrel `5`, `6`, `7` értékeket is megkülönböztet, ezért a `+0x30` numerikus kódként való olvasata egyezik. A kódok neve és a gyűjteményfajták kapcsolata nem állapítható meg.
- **PicasaPy-út.** A controller forrása közvetlenül megnevezi a `folder` és `album` kártyafajtát, és nem készít más fajtát. Ez önálló implementációs bizonyíték, de a bináris számaihoz nincs megfeleltető kapocs.

**Cáfoló kísérlet.** Megpróbáltam cáfolni, hogy a `+0x0c == 2` egyszerűen az albumtípust, a qshow `+0x30 == 1` pedig a mappatípust jelenti. A `0x004b8470` az album/mappa különbséget másik mezőn, a `+0x9d` kapcsolón keresztül kezeli, míg a `+0x0c` kódot a `0x004b29d0` önállóan olvassa. A `0x006dc4c0` ezenkívül a qshow-rekord `+0x30` mezőjén több, `5`, `6`, `7` értéket is külön kezel. A próba cáfolta a két kód automatikus album/mappa címkézését, de nem bizonyította, melyik gyűjteménytípus mely kódot kapja. A negatív eredmény nem a binary-index hiányára, hanem a vizsgált utasítások és a külön hívó összevetésére épül.

**Bizonyítottsági fok.** A mezőíró címe, a `+0x0c == 2` qshow előfeltételként való működése, a qshow numerikus kapui és a PicasaPy által készített két kártyafajta **megerősített**: külön gépikód- és hívó/fogyasztó út egyezik, a PicasaPy-t pedig közvetlen forrás igazolja. A `2` tartalmi jelentése, a `+0x30` kódok és a `+0x18` mező neve, a teljes eredeti gyűjteményhalmaz és a típusok közti implementációs eltérés **nyitott**. A teljes #6532 kutatási feladat emiatt nem zárult le.

**A #6532 „Kész, ha” pontjai.** (1) ✅ Eredeti videó rendelkezésre áll a helyi job-373 és job-446 felvételekből; a 38.2.101 és 38.2.104 dokumentálja őket. Ebben a körben új felvétel nem készült. (2) ⛔ A státuszmező írója és a qshow numerikus kapui címmel igazoltak, de a kapuk gyűjteménytípusa, a teljes forráshalmaz, a kártyák és a vezérlők minden látható részének bináris feltárása továbbra sem teljes. (3) ⛔ PicasaPy jelenleg mappa- és nem üres albumkártyáit összevetettem, de a numerikus bináris kódok nem nevezik meg az eredeti típusokat, így tételes típus-összevetés nincs. (4) ⛔ A meglévő #6713 fejlesztési jegy a korábbi kutatási állapotban meg van nevezve, de a nyitott státusza ebben a GitHub nélküli körben nem ellenőrizhető. A kiadási összehasonlító anyag és az új, itt még nem igazolt típusmegfeleltetéshez tartozó fejlesztési jegy nincs.

**Javasolt jegytörzs-bővítés.** A mezőíró és a kapufeltételek bizonyítottak, de az ismeretlen típusnevek miatt ebből a körből nem készül pontos fejlesztői változtatási lista. A következő adatot érdemes a #6532-be felvenni: a `0x004ab520` a `CAlbumState+0x138 + index*0x24 + 0x0c` mező írója; az érték `2` a `0x004b29d0` qshow-előfeltétele; a qshow a 0x38 bájtos rekordból csak `+0x30 == 1` és `+0x18 == 0` esetén kér kártyaadatot (`0x007fc7c0`). Ezek emberi jelentése és a PicasaPy mappa/album kártyáival való megfeleltetése **NINCS MEG**. A következő kutatási kör a `0x004aa9f0` és `0x004b1a90` célzott Ghidra-kimenetével döntheti el, hogy indokolt-e fejlesztői eltérés.

**Új kutatási jegyjavaslatok.** Nincs. A maradék kérdések a #6532 feladatán belül vannak.

**Nyitott.**

- A `0x004aa9f0` és `0x004b1a90` célzott dekompilációja elkészült 2026-11-11-én. A kapott kimenet igazolja a mezők gépi kezelését, de nem nevezi meg a `+0x0c` állapotkódok és a `+0x30` rekordkódok gyűjteménytípusait. A pontosítás a 38.2.111 szakaszban van; az új eredmény nem zárja le ezt a szemantikai kérdést.
- A teljes eredeti gyűjteményhalmaz és a PicasaPy mappa/album/egyéb listájával való azonosság: **NINCS MEG**. A megszerzéshez a fenti mezőnevek feloldása, majd ugyanazon könyvtár descriptor- és kártyalistájának összevetése kell.

**Módosított fájlok ebben a szakaszban.** A 38.2.109 mezőíróra és típusjelentésre vonatkozó nyitott sorait a 38.2.110 pontosítja. A 38.2.110 dokumentálja a `+0x0c` írót, a qshow kapukat, a PicasaPy kategóriahalmazát és a megmaradt blokkoló kérdéseket. Kódot, tesztet, eredeti binárist, videót vagy mérőadatot nem módosítottam.

#### 38.2.111 Gyűjteményállapot és a köztes rekordkódok (#6532, 2026-11-11)

**Hatókör és módszer.** A vizsgálat a `2026-11-11-6532-colab-decomp-5.txt`, `2026-11-11-6532-colab-158-30-irok.txt`, `2026-11-11-6532-colab-decomp-3.txt` és `2026-11-10-6532-colab-decomp.txt` Ghidra-kimeneteit, a binary-index string-xrefjeit, valamint az eredeti bináris célzott `annot_disasm.py` olvasását kapcsolta össze. Az utasításokat külön útvonalként ellenőriztem a Ghidra-C mellett. Nem készült új Ghidra-kör vagy futásidejű gyűjteménylista.

**A `CAlbumState +0x0c` állapotkódjai.** A `0x004ab520` a `CAlbumState +0x138 + index*0x24 + 0x0c` mező írója. A `0x004a8bb0` a `1` értéket `3`-ra, a `2` értéket `4`-re; a `0x004a8bf0` a `3` értéket `1`-re, a `4` értéket `2`-re váltja. A `0x004aa9f0` a sor metaadatait és több szolgáltatói feltételt vizsgálva hívja ezeket az átmeneteket, illetve ír `0` vagy `1` értéket. A `0x004aae90` útja `2`-t is írhat a sorba. A `0x004a8a30` hívó soronként futtatja a `0x004aa9f0`-et, majd összeveti a `+0x0c` értéket a korábbival. Ez állapotmezőt és állapotfrissítést igazol, nem gyűjteménytípust.

A `0x004b8470` a mappa/album útvonalat külön `+0x9d` mezővel és a `0x004461a0` predikátummal kezeli. A `0x004b29d0` csak akkor épít 0x38 bájtos rekordot a `CAlbumState` sorból, ha a `+0x0c == 2`. A kód `2` szükséges továbbítási állapot ezen az útvonalon. Nincs bináris bizonyíték arra, hogy a `2` egy adott gyűjteménytípus neve volna.

**A `+0x158` listában szereplő 0x38 bájtos rekordok.** A közös építő `0x004a0720` az első argumentumát a rekord `+0x30` mezőjébe, a harmadik argumentumát a `+0x18` byte-ba írja. A `0x004ae600` e mezőket másoláskor megőrzi. A qshow `0x007fc7c0` csak azt a rekordot veszi fel a kártyalistájába, amelynél `+0x30 == 1` és `+0x18 == 0`.

| Kód vagy mező | Binárisból igazolható kapcsolat | Gyűjteménytípus jelentése |
|---|---|---|
| `CAlbumState +0x0c == 2` | A `0x004b29d0` ezen a kapun át készít köztes rekordot; a `0x004ab520` írja az állapotmezőt. | **NINCS MEG.** Állapotkód, nem bizonyított típusnév. |
| rekord `+0x30 == 1` | A `0x004b29d0` ezt adja át a közös rekordépítőnek; a qshow `0x007fc7c0` ezt fogadja el kártyakapuként. | A `CAlbumState` út rekordja, a mappa/album konkrét megfeleltetése **NINCS MEG**. |
| rekord `+0x30 == 5` | A `0x004b1c80` ezt hozza létre a `0x004b6190` `Folders` faépítő útjában. | A folder-fa út rekordja, de az `5` általános gyűjteménytípus jelentése **NINCS MEG**. A qshow kártyakapuján nem megy át. |
| rekord `+0x30 == 6` vagy `7` | A `0x006dc4c0` a getterből olvasott rekordokon külön kezeli ezeket a számokat. | A létrehozó és a gyűjteménytípus **NINCS MEG**. |
| rekord `+0x18` | A `0x004a0720` harmadik argumentumának byte-ja; a qshow `0` értéket követel meg. A `0x004b1c80` kód `5` létrehozásakor `!bVar14` kerül ide. | A mező pontos neve és üzleti jelentése **NINCS MEG**. |

A `0x004b1c80` a `Folders` fa felől valóban létrehoz `+0x30 == 5` rekordot. Ugyanott a `6` és `7` számot egy helyi változó kapja meg bizonyos rekordtulajdonságok alapján, de nem ezek kerülnek a rekord `+0x30` mezőjébe. A `0x006dc4c0` fogyasztó oldalról mutatja, hogy az `5`, `6`, `7` külön kód, másik ágban az `1`, `5`, `6`, `7` egy csoportként elfogadott. Ez a vizsgálat nem nevezi meg a kódokhoz tartozó felhasználói műveletet.

**Kategóriacímkék és a PicasaPy összevetése.** A `0x004abe70` út karakterlánc-xrefjei között szerepel a `Folders on Disk`, `My Albums`, `Exported Pictures`, `Other Stuff`, `Labels`, `People`, `Screensaver`, `Starred Photos`, `Recently Updated`, `Emailed`, `Uploaded`, `Outlook` és `Hello Albums~`. Ez azt igazolja, hogy a descriptorépítő környezet ismeri ezeket a címkéket, de nem kapcsolja őket az egyes `+0x158` rekordok `+0x30` kódjaihoz, és nem bizonyítja, melyek jutnak a qshow kártyalistájába.

A jelenlegi `src/picasapy/app/timeline_controller.py:269-299,357-382` kódja csak mappa- és nem üres albumkártyákat épít, és a gyűjtemény legkorábbi EXIF `datetime` értékét használja. A `:293-299` a teljes `datetime` értéket is használja a rendezésben; napra vetített `toordinal()` csak a csúszkakoordinátához kerül a `:301-320` sorokban. Ez felülírja a 38.2.109 azon akkori állítását, hogy a jelenlegi forrás `.date()`-tal napra csonkolja a dátumot. A bináris kódok és a PicasaPy mappa/album fajtái közötti azonosítás hiányában tényleges típuseltérés **nem igazolódott**.

**Két független bizonyítási út.**

- **A út, CAlbumState.** A `0x004ab520` utasításszintű írása és a `0x004a8bb0`, `0x004a8bf0`, `0x004aa9f0` külön hívói/átmenetei ugyanazt a `+0x0c` mezőt használják. A független `0x004b29d0` fogyasztó `2` értéket követel meg. Az utak egyeznek abban, hogy ez változó állapotkód és qshow-előfeltétel; az emberi típusnév egyikből sem olvasható ki.
- **B út, köztes rekord.** A `0x004a0720` argumentumai a `+0x30` és `+0x18` mezőbe kerülnek; a `0x004ae600` továbbmásolja ezeket; a `0x007fc7c0` a `1/0` értékeket a kártyakapuként ellenőrzi. A `0x004b1c80` külön, `Folders` útvonalon hoz létre `5` kódú rekordot, míg a `0x006dc4c0` több kódot fogyaszt. Az utak egyeznek a kódok gépi szerepében, a kategórianevek megfeleltetése nyitott.
- **PicasaPy-forrás.** Független alkalmazásrétegként közvetlenül igazolja, hogy jelenleg csak `folder` és `album` kártya készül. Bináris megfeleltető adat nélkül nem bizonyítja, hogy az eredeti lista ugyanezt vagy ennél többet tartalmaz.

**Cáfoló kísérlet.** Próbáltam cáfolni, hogy a `+0x30` azonos eltolása minden találatnál azonos gyűjteménytípust jelent. A `0x006f4ea0` talált írás RTTI-je `LHUpload`, szövegkörnyezete feltöltési állapotokhoz tartozik, nem a CThumbUI qshow listájához. A `0x004b1c80` kód `6` és `7` értékei pedig helyi változóba íródnak, nem a rekord `+0x30` mezőjébe. A cáfolat ugyanúgy közvetlen utasításokra, függvénykörnyezetre és RTTI-re épül, nem az index negatív találatára. Így az offset önmagában nem elég a típusmegfeleltetéshez.

**Bizonyítottsági fok.** A `+0x0c` állapotmező írója és átmenetei, a `2` qshow-előfeltétele, a rekordépítő argumentumok, a qshow `+0x30 == 1` és `+0x18 == 0` kapuja, továbbá az `5` kódú `Folders` faút **megerősített**. A `1`, `5`, `6`, `7` rekordkódok teljes gyűjteménytípus-megfeleltetése, a `+0x18` szemantikája, valamint az eredeti és PicasaPy gyűjteményhalmaz teljes összevetése **nyitott**. A #6532 e részének összesített bizonyítottsága ezért **feltételes**.

**A #6532 „Kész, ha” pontjai.** (1) ✅ A korábbi felvételeket a 38.2.101 és 38.2.104 szakasz dokumentálja; ebben a körben új videó nem készült. (2) ⛔ A vizsgált állapot- és rekordkapuk címmel igazoltak, de a kódok típusnevei és a teljes qshow forráshalmaz nyitott. (3) ⛔ A PicasaPy mappa/album halmaza dokumentált, de eredeti típusmegfeleltetés hiányában teljes pontonkénti összevetés nincs. (4) ⛔ Az előzményben szereplő #6713 megvalósítási jegy státusza GitHub nélkül nem ellenőrizhető; ebből a körből nem igazolódott új fejlesztési eltérés, ezért új fejlesztői jegy nem indokolt. A kiadási összehasonlító videó vagy képsor ebben a körben nem készült.

**Javasolt jegytörzs-bővítés.**

> Az új Ghidra-kimenet a `CAlbumState +0x0c == 2` állapotot a qshow egyik listaépítési előfeltételeként igazolja (`0x004b29d0`), de nem gyűjteménytípusként. A 0x38 bájtos köztes rekord `+0x30 == 1` és `+0x18 == 0` feltételekkel jut a qshow kártyalistájába (`0x004a0720`, `0x004ae600`, `0x007fc7c0`). A `+0x30 == 5` kód a `Folders` faépítő útban keletkezik (`0x004b1c80`, `0x004b6190`), a `6` és `7` forrása, valamint a `+0x18` üzleti jelentése továbbra sem bizonyított. A PicasaPy jelenlegi vezérlője csak mappa- és nem üres albumkártyát épít (`src/picasapy/app/timeline_controller.py:269-299`). Ebből a körből nincs bizonyított fejlesztési eltérés, ezért kódmódosításra vonatkozó feladatlista nem adható. A teljes eredeti típuslista és a PicasaPy megfeleltetés maradjon nyitott kutatási feladat.

**Új kutatási jegyjavaslatok.** Nincs külön jegyjavaslat; a nyitott típusmegfeleltetés és halmaz-összevetés a #6532 tárgykörébe tartozik.

**Nyitott.**

- `Ghidra-kör kell: 0x004b0fb0 - a 0x004b6190 Folders útjából hívott rekurzív összesítő hogyan jut rekordhoz, és van-e olyan kimeneti útja, amely a +0x158 listába +0x30 == 6 vagy 7 értéket tesz, illetve milyen felületi gyűjteményhez tartozik [blokkoló]`. A `2026-11-11-6532-colab-158-30-irok.txt` a `0x004b6190` hívását mutatja, de a `0x004b0fb0` függvényt nem dekompilálja. A helyi diszasszemblálás önmagában csak rekurzív összesítést igazol, rekordtípust nem.
- A `+0x18` byte pontos jelentése és az 1, 5, 6, 7 kódok valamennyi létrehozó útjának típusneve: **NINCS MEG**.
- A `CAlbumState +0x0c` kódok felhasználói jelentése, különösen hogy milyen rekordoknál áll elő a `2`: **NINCS MEG**. A `0x004aa9f0` és `0x004aae90` dekompilációi a mezőállapot frissítését mutatják, a gyűjteménytípushoz kapcsoló feltételt nem nevezik meg.
- Az eredeti qshow teljes gyűjteményhalmaza és az egyező minta PicasaPy kártyáival végzett mérés: **NINCS MEG**.

**Módosított fájlok ebben a szakaszban.** Ez a 38.2.111 szakasz dokumentálja a 2026-11-11-i Ghidra-forrásokat, a célzott diszasszemblálás és string-xref ellenőrzést, a cáfoló kísérletet, a PicasaPy jelenlegi kódállapotát és a maradék kérdéseket. Kódot, tesztet, eredeti binárist, videót vagy mérőadatot nem módosítottam.

#### 38.2.112 A köztes rekord nyolc hívójának kódjai és qshow-kapui (#6532, 2026-11-11)

**Kérdés és hatókör.** A `0x004a0720` mind a nyolc hívójának argumentumaiból megállapítható-e a köztes rekord `+0x30` kódja, `+0x18` értéke és a hívó gyűjteményi környezete, majd ezekből melyik környezet jut át a qshow szűrőin? A kérdés az összes közvetlen hívó kódútját fedi, nem az összes futásidejű `CAlbumState`-sor nevét.

**Módszer.** A `2026-11-11-6532-colab-004a0720-hivok.txt` mind a nyolc hívó dekompilációját, a `2026-11-11-6532-colab-decomp-6.txt` pedig a rekordépítőt, a qshow útban hívott `0x004b0fb0` függvényt és a hívólistát adja. Az argumentumokat célzott `annot_disasm.py` olvasattal ellenőriztem a hívási helyeken. A qshow kapuját a `0x007fc7c0` külön diszasszemblálása igazolja. Teljes `.text` pásztázás nem történt.

**A mezők jelentése.** A `0x004a0720` első argumentumát dwordként a 0x38 bájtos köztes rekord `+0x30` mezőjébe, harmadik argumentumát byte-ként a `+0x18` mezőbe írja. A `CAlbumState` forrásrekord `+0x0c == 2` feltétele egy másik rekord másik mezője, amelyet a `0x004b29d0` a köztes rekord építése előtt ellenőriz. A három kaput nem szabad egyetlen rekord mezőiként összevonni.

| Hívó és hely | `+0x30` | `+0x18` | Binárisból igazolható hívási környezet | Qshow-eredmény |
|---|---:|---:|---|---|
| `0x004b29d0`, `0x004b2ab4` | `1` | `0` | `CAlbumState`-sor továbbítása. A forrás sor `+0x0c` mezője `2` kell legyen; a `0x004b8470` út opcionálisan mappa/album predikátumot is alkalmaz. | Átjut, ha a forrásállapot és a további lista-feltételek is teljesülnek. |
| `0x004b2e10`, `0x004b2f9a` | `3` | a forrássor `+0x1d` byte-ja | Állapothoz kapcsolódó kiegészítő rekord, a `state`, `super:` és `(%d)` szövegkörnyezetben. | Nem jut át, a `+0x30` érték nem `1`. |
| `0x004b2e10`, `0x004b3281` | `0` | `param_1` alsó byte-ja | Állapotváltozás alatti kiegészítő rekord. | Nem jut át. |
| `0x004b3770`, `0x004b3886`, `0x004b3b50`, `0x004b3f4b` | `2` | `1` | Albumépítő `Updated` út; karakterlánc-xref: `Updated ` és `CAlbumBuilder::updated`. | Nem jut át. |
| `0x004b34a0`, `0x004b35a2` | `2` | `1` | A `0x004b3770` albumépítő segédútja. | Nem jut át. |
| `0x004b1c80`, `0x004b1eac` | `5` | `!bVar14` | A `0x004b6190` `Folders` faútja. | Nem jut át. |
| `0x004b1c80`, `0x004b22ce` | `2` | `1` | A `Folders` fa gyermek/alrekordja. | Nem jut át. |
| `0x004b1a90`, `0x004b1acb` | `8` | `0` | A `0x004b1c80` hívója, a `Folders` faág segédrekordja. | Nem jut át. |
| `0x004b80d0`, `0x004b81fd` | `2` | `1` | Peer/public-host felsorolás; `ytPeerHost` és `public/` szövegkörnyezet. | Nem jut át. |
| `0x004b7f00`, `0x004b7f17` | `9` | `0` | A `0x004b80d0` public-host alútja. | Nem jut át. |

A sorok összesen 12 közvetlen hívási helyet fednek le. A `+0x18` két esetben futásidejű byte-tól függ: a táblázat a ténylegesen átadott kifejezést adja meg, nem helyettesíti becsléssel.

**A `0x004b0fb0` korábbi nyitott kérdése.** A `2026-11-11-6532-colab-decomp-6.txt` teljes dekompilációja szerint ez a függvény rekurzívan összesíti a gyermekrekordok dátumát és számlálóit. Nem hívja a `0x004a0720` rekordépítőt. A saját összesítő csomópontján ír `+0x30` eltolásra egy double értéket, de ez nem a 0x38 bájtos köztes rekord `+0x30` kódmezője; a függvény nem állít elő `+0x30 == 6` vagy `7` rekordot. A `0x004b6190` Folders-ágából való meghívása tehát nem nyit ilyen rekordlétrehozó utat. A korábban erre a függvényre irányuló Ghidra-kérés lezárható a meglévő dekompilációval.

**Mit jelent a kapu a gyűjteményhalmazra.** A nyolc hívó numerikus és hívási-környezeti leltára teljes. E leltárban egyedül a `0x004b29d0` generikus `CAlbumState`-listaút ad `+0x30 == 1`, `+0x18 == 0` rekordot. A `Folders` fa saját `5`, `8` és `2` kódú rekordjai, az `Updated` albumépítő, valamint a peer/public-host út `2` és `9` kódjai nem mennek át ezen a qshow kapun. A `+0x18 == 0` értéket önmagában adó kód `8` és `9` sem elég.

Ez lezárja azt a szűk kérdést, hogy a nyolc rekordépítő hívó közül melyik kódcsoport felel meg a qshow kapujának. A numerikus hívó/környezet leltár teljes, de a kód és felületi gyűjteménytípus közötti tábla nem teljes, ezért a #6532 teljes gyűjteményhalmaz-kérdése nem zárult le. A `+0x30 == 1` út a `CAlbumState` által kiválasztott sort fogadja el, de a mostani hívó-argumentumok nem nevezik meg, hogy ebből melyik sor a `Folders on Disk`, album, `People`, `Starred Photos`, `Uploaded` vagy más felületi kategória. E kategórianevek előfordulása a `0x004abe70` építőútban önmagában nem bizonyítja, hogy mely soruk kap `CAlbumState +0x0c == 2` állapotot és jut be a qshow listájába. A típusonkénti teljes forráshalmaz **NINCS MEG**.

**PicasaPy-összevetés.** A `src/picasapy/app/timeline_controller.py` `TimelineController._collections_to_qml()` mappánként képez kártyát, majd az albumok közül csak a nem üreseket adja hozzá (`:269-299`). Az eredeti job-239 felvétel dokumentált képkockáin mappák és a `Recently Updated` nevű elem látható (`38.2.81`). A kódút-leltár megerősíti a mappa/album adatút egy részét, de nem köti az összes látható nevet a `+0x30 == 1` rekordhoz; a PicasaPy és a teljes eredeti halmaz közötti hiány vagy többlet ezért nem bizonyított. Új fejlesztési eltérés ebből a körből **nem igazolódott**.

**Független bizonyítási utak.**

- **A út, Ghidra.** A `2026-11-11-6532-colab-004a0720-hivok.txt` dekompilációinak 12 hívási helye megadja a közös rekordépítő argumentumait és a hívók szövegkörnyezetét. A `2026-11-11-6532-colab-decomp-6.txt` megadja, mely mezőbe kerül az első és harmadik argumentum.
- **B út, helyi bináris.** A hívási helyek célzott diszasszemblálása ellenőrzi az átadott konstansokat és változókat. A `0x007fc7c0` külön kódútja a `+0x30 == 1`, `+0x18 == 0` feltételt vizsgálja; a `0x004b8ee0 -> 0x004b8470 -> 0x004b29d0` hívási lánc a `CAlbumState +0x0c == 2` előfeltételt külön igazolja. A dekompiláció és az utasítás/xref út egyezik.
- **C út, alkalmazás és mérés.** A PicasaPy controller saját forrása mappát és nem üres albumot képez. A job-239 mérés mappaneveket és egy `Recently Updated` nevű elemet mutat. Ez függetlenül megerősíti, hogy mindkét általános felületi forma megjelenik, de nem bizonyítja az eredeti katalógus teljességét vagy a meg nem figyelt kategóriák hiányát.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a köztes rekord `+0x30` kódja egyetlen felhasználói gyűjteménytípust jelöl. A `2` érték három elkülönülő környezetben szerepel: `Updated` albumépítőben (`0x004b3770`), `Folders` fa gyermekrekordjaként (`0x004b1c80`) és peer/public-host felsorolásban (`0x004b80d0`). A hívók dekompilációi és a helyi hívásutasítások mindhárom konkrét értéket megerősítik. Az egy kód és egy gyűjteménytípus feltevés cáfolódott; ezért a kódokból önmagukban nem szabad felhasználói kategórianév-készletet következtetni.

**Bizonyítottsági fok.** A köztes rekord mezőírása, mind a nyolc hívó tizenkét argumentumátadása, a kód-környezet párosítás és a qshow numerikus kapuja **megerősített**: a Ghidra-kimenet és az utasításszintű ellenőrzés egyezik. A teljes eredeti gyűjteményhalmaz és annak PicasaPy-listával való teljes egyezése **nyitott**, mert a generikus `CAlbumState +0x0c == 2` sorokat nem kötöttük minden felületi kategóriához.

**A #6532 „Kész, ha” pontjai.** (1) ✅ Az eredeti felvételek job-373 és job-446 anyagát a 38.2.101 és 38.2.104 szakasz dokumentálja; ebben a körben új videó nem készült. (2) ⛔ A nyolc hívó rekordkódja és qshow-kapuja címmel igazolt, de a teljes típusonkénti forráshalmaz és több korábban nyitott időzítési részlet még nincs lezárva. (3) ⛔ A PicasaPy mappákat és nem üres albumokat listáz; az összes eredeti felületi típusra teljes, tételes összevetés nincs, és új fejlesztési eltérés nem bizonyított. (4) ⛔ Kiadásba adható, PicasaPy-val párhuzamos összehasonlító videó vagy képsor nincs dokumentálva. A gyűjteményhalmaz-kérdés szűk hívó/kódkapu része lezárult, a teljes #6532 elfogadási feltétel nem.

**Javasolt jegytörzs-bővítés.**

> A `0x004a0720` mind a nyolc hívójának argumentumai és a qshow szűrői a `docs/specs/picasa-idorend-bemutato-kutatas.md` 38.2.112 szakaszában vannak dokumentálva. A 12 hívási helyből egyedül a `0x004b29d0` generikus CAlbumState-út ad qshow által elfogadott `+0x30 == 1`, `+0x18 == 0` rekordot, és ehhez a forrássor `+0x0c == 2` állapota is kell. A Folders-fa, Updated albumépítő és peer/public-host rekordkódjai ezen a kapun nem mennek át. A `0x004b0fb0` rekurzív összesítő, nem rekordépítő. Az eredeti teljes forráshalmaz nyitott marad: a generikus CAlbumState sorok felhasználói kategóriákhoz kötése még nincs bizonyítva. A PicasaPy mappa- és nem üres albumkártyáit építi (`src/picasapy/app/timeline_controller.py:269-299`); e kutatási körben konkrét típuseltérés nem igazolódott.

**Új kutatási jegyjavaslatok.** Nincs külön jegyjavaslat; a megmaradt kategória-tagsági kérdés a #6532 teljes forráshalmazának része.

**Nyitott.**

- A `CAlbumState +0x138` sorok felhasználói kategóriája és a `+0x0c == 2` állapotba kerülő sorok teljes listája **NINCS MEG**. A következő bizonyíték a kategórianévvel és ugyanazon sor állapotkódjával együtt rögzített futásidejű lista vagy az építő és a sorállapot közötti teljes adatút.
- A People, Starred Photos, Uploaded és egyéb speciális csoportok qshow-tagsága **NINCS MEG**. A `0x004abe70` kategórianév-xrefje önmagában nem bizonyít tagságot.
- A PicasaPy teljes gyűjteménylistájának és az eredeti qshow teljes listájának ugyanazon katalóguson mért egyezése **NINCS MEG**.
- A billentyűesemények első és utolsó mozgó képkockához kötése, valamint a Wine futás tényleges Preferences-értékei továbbra is nyitottak (`38.2.104`).

**Módosított fájlok ebben a szakaszban.** A 38.2.112 az új Ghidra-kimenetek alapján lezárja a `0x004a0720` nyolc hívójának kód- és kapu-leltárát, frissíti a `0x004b0fb0` nyitott kérdését, és megőrzi a teljes felhasználói kategóriahalmazt nyitottként. Kódot, tesztet, eredeti binárist, videót vagy mérőadatot nem módosítottam.

#### 38.2.113 A Recently Updated időablaka és nyitott rekordkapcsolata (#6532, 2026-11-11)

**Kérdés és hatókör.** A `Recently Updated` / `CThumbDB::RecentUpdate` / `]updated` kulcs útján meghatározható-e a gyűjtemény tagsága, elemszáma, sorrendje és qshow-beli CAlbumState kapcsolata? A vizsgálat a `0x0055ece0` helyi utasításait, a már meglévő Ghidra-kimeneteket, az index pozitív string-xrefjeit, a job-239 korábban dokumentált képkockáját és a PicasaPy forrását kapcsolja össze. Teljes `.text` pásztázás és új futásidejű adatfelvétel nem történt.

**Kategória létrehozása és kulcsa.** A `0x004a66e0` `FastStart == 0` ágában meghívja a `0x004abe70`-et. Ennek meglévő Ghidra-dekompilációjában a `CThumbDB::RecentUpdate` címke után a `0x004ad220(in_EAX, "]updated", 0, 0)` hívás szerepel. Az eredeti bináris pozitív xrefje a `"]updated"` karakterláncot a `0x004abe70` és `0x0055ece0` függvényekben is megtalálja. Ez bizonyítja a kulcs regisztrációs és fogyasztói útját, de nem köti még ugyanahhoz a futásidejű CAlbumState-sorhoz.

**Dátumszűrő.** A `0x0055ece0` `0x0055f08e`-`0x0055f0bd` ága a CThumbDB rekordlekérője (`0x004edf60`) által kitöltött descriptor `+4/+8` qwordját a `0x0098b650` függvénynek adja. Ez a segéd Windows `FILETIME`-ot helyi időre alakít Picasa-dátummá. A másik operandust a `0x0098b770(7)` állítja elő. A `0x0098b770` meghívja a `__time64` rutint (`0x00c0a421`, import/xref: `GetSystemTimeAsFileTime`), majd az aktuális `__time64` értékből kivonja a hívó `EAX=7` argumentumának 86400 másodperces napokkal vett szorzatát (`0x15180`). Az eredményt Picasa-dátummá kódolja a `0x0098b550`-en. A `fcomp` ág csak a küszöbnél szigorúan későbbi rekorddátumot engedi tovább ebbe a szűrőágba. A küszöb képzésekor a kivonás 604800 másodperc; a rekord és a küszöb összehasonlítása helyi naptári időként történik, ezért az összehasonlított értékek alapján a teljes tagsági ablak minden időzóna-átmenetre nem nevezhető további bizonyítás nélkül pontosan 604800 eltelt másodpercnek. Lásd 38.2.119.

A `0x0055ece0` ezen ágában a `0x004edf60` descriptor típusmezőjének `0x15`, `0x17`, `0x18` és `0x1a` értékei kihagyják ezt a dátumellenőrzést. A rutin más előfeltételei és a rekord `FILETIME` mezőjének üzleti jelentése nem teljesen tisztázott; ezért a hét napos feltétel a vizsgált ág bizonyított feltétele, nem a teljes albumtagság leírása.

**Elemszám és sorrend.** A `0x0055f0db`-`0x0055f101` út a `RecentLimit` beállítást `0xfa` alapértékkel olvassa. A `0x0055f162`-`0x0055f191` az elemszámot ehhez a limithez hasonlítja, és túllépéskor ismételten eltávolítja az utolsó indexű elemet a `0x006caf20` hívásával. Az alapérték mellett a megőrzött lista legfeljebb 250 elemes; beállított `RecentLimit` esetén annak értéke érvényesül. A `0x0055ece0` a bemeneti indexeket növekvő sorrendben járja be, a `0x006c9e80` pedig a `]updated` listába `0` pozícióra teszi az elfogadott elemet, a már bent lévő azonos elemet előbb eltávolítva. Emiatt az eredmény a bemeneti bejárás fordított sorrendje. A bemeneti tömb tényleges sorrendje és ennek dátumhoz való viszonya **NINCS MEG**. A hét napos forrás-időbélyeg üzleti jelentése, például fájlmódosítás vagy importesemény, **NINCS MEG**.

**CAlbumState és qshow határa.** A `0x004b8ee0`/`0x004b8470` út CAlbumState sorokat gyűjt, a `0x004b29d0` pedig csak a forrássor `+0x0c == 2` állapotánál készít qshow rekordot. Ezzel szemben a `0x004b3770` `CAlbumBuilder::updated` út hívóhelyei (`0x004b3886`, `0x004b3b50`, `0x004b3f4b`) a `0x004a0720` hívásain keresztül a különálló köztes rekord `+0x30` mezőjébe `2` értéket írnak (`38.2.112`). A qshow szűrője (`0x007fc7c0`) `+0x30 == 1` és `+0x18 == 0` rekordot fogad el. A két különböző rekord `2` mezőértéke nem azonosítható egymással. A `0x004b3770` út hónap-éves `Updated` címkéje ezért önmagában nem bizonyítja a `Recently Updated` album CAlbumState-sorának qshow-hoz jutását.

A job-239 `kepernyo__02.png` képkockáján az eredeti Picasa `Albums (1)` alatt `Recently Updated (24)` látszik, és a qshow-léptetésben ugyanez a címke utolsóként megjelenik (`38.2.81`). Ez egy mért futás címkéje és darabszáma, nem a 24 kép azonosítója vagy a bináris tagsági szabálya. A PicasaPy `TimelineController._collections_to_qml()` mappákat és nem üres albumokat ad a listához (`src/picasapy/app/timeline_controller.py:269-299`); az alkalmazás forrásában nem találtam `Recently` szöveget. Különleges `RecentUpdate` albumépítő út nincs igazolva a PicasaPy forrásában.

| Állítás | Forrás |
|---|---|
| A `FastStart == 0` ág és a `CThumbDB::RecentUpdate` / `]updated` kategória felvétele. | bináris (`0x004a66e0`, `0x004abe70`, `0x004ad220`; meglévő Ghidra-kimenet `2026-11-11-6532-colab-decomp-3.txt`) |
| A `]updated` kulcs fogyasztói ága, a `7 * 86400 = 604800` másodperces gördülő küszöb és a szigorú dátum-összehasonlítás. | bináris (`0x0055ece0`, `0x0098b770`, `0x0098b650`, import `0x00c0a421`, `0x0098b550`) |
| A hét napos dátumtesztet kihagyó descriptor típusok: `0x15`, `0x17`, `0x18`, `0x1a`. | bináris (`0x0055ece0`, `0x004edf60`) |
| A dátummező rekordon belüli helye: descriptor `+4/+8`, FILETIME alak. | bináris (`0x004edf60`, `0x0055ece0`, `0x0098b650`) |
| A `RecentLimit` alapértéke `0xfa = 250` elem, a beállított érték felülírhatja. | bináris (`0x0055ece0`, `0x0055f162`, `0x006caf20`) |
| A `0x004b3770` hívóhelyei `+0x30 == 2` köztes rekordot készítenek, amit a qshow `+0x30 == 1` kapuja nem fogad el. | bináris (`0x004b3886`, `0x004b3b50`, `0x004b3f4b`, `0x007fc7c0`; részletek: 38.2.112) |
| A qshow forrássor `+0x0c == 2` előfeltétele, és a külön köztes rekord `+0x30 == 1`, `+0x18 == 0` kapuja. | bináris (`0x004b29d0`, `0x007fc7c0`) |
| Job-239 katalógusban a címke és a 24-es darabszám. | mérés (`job-239/kepernyo__02.png`, 38.2.81) |
| A job-373 és job-446 eredeti videó rendelkezésre állása. | mérés (38.2.101, 38.2.104) |
| PicasaPy által épített mappa- és nem üres albumkártyák. | mérés (forrásleolvasás: `src/picasapy/app/timeline_controller.py:269-299`) |
| Külön `Recently Updated` építőút hiánya a PicasaPy Időrend forrásában. | mérés (forrásleolvasás: `src/picasapy/app/timeline_controller.py:269-299`; `rg -n 'Recently' src/picasapy` üres eredmény) |
| A descriptor FILETIME eseményjelentése, a teljes tagsági feltétel és a rendezési kulcs. | NINCS MEG |
| A `Recently Updated` CAlbumState-sor `+0x0c == 2` állapotba írása és annak útja a qshow-hoz. | NINCS MEG |

**A két független út.** A út: a `0x0055ece0` utasításai átadják a `7` értéket a `0x0098b770`-nek, FILETIME dátumot hasonlítanak a küszöbhöz, majd a `RecentLimit` alapján darabszámot korlátoznak. B út: az import/xref-adat a `0x00c0a421` címet `GetSystemTimeAsFileTime` forrásként azonosítja; a külön dátumkódoló/dekódoló út a `0x0098b320` és `0x0098b550` címeken 86400 másodperces napot és 1899-12-30 kezdőnapot igazol (`38.2.108`). A két út egyezik a hétnapos küszöb dátumreprezentációjában. Ez nem azonosítja a rekordidő üzleti eseményét vagy a teljes lista rendezését.

**Cáfoló kísérlet.** Azt a feltevést próbáltam cáfolni, hogy a `7` egy évet vagy a `250` napot jelent. A `0x0098b770` `7 * 0x15180` aritmetikája, az aktuális `__time64` értékből történő kivonása és az utána következő dátumkódolás a `7` értéket napokban mért időtartamként azonosítja. A `RecentLimit` utáni elemszám-összehasonlítás és az utolsó index ismételt törlése a `250` értéket elemszámkorlátnak azonosítja. Az alternatív olvasatot a hívó és segéd utasításai külön is alátámasztják. Azt a feltevést is ellenőriztem, hogy `CAlbumBuilder::updated` maga a Recently Updated lista: az általa előállított `+0x30 == 2` köztes rekord qshow `+0x30 == 1` feltételén nem megy át. Ezt a két út külön rekordmezőinek ellenőrzése cáfolja.

**Bizonyítottsági fok.** A `]updated` kulcs használata, a hét napos időhatár és a `RecentLimit` alapértelmezett 250-es elemkorlátja binárisból igazolt. A teljes albumtagság, az időbélyeg eseményjelentése, a rendezés, a frissítés kiváltója és a CAlbumState/qshow kapcsolat **nyitott**. Az összes kért részre vonatkozó kutatás ezért **feltételes**, nem teljes.

**A #6532 „Kész, ha” pontjai.** (1) ✅ Eredeti videó elérhető és dokumentált a job-373 és job-446 alapján (`38.2.101`, `38.2.104`); ebben a körben új felvétel nem készült. (2) ⛔ A Recently Updated ághoz a hét napos küszöb és elemszámkorlát igazolt, de a mező eseményjelentése, teljes tagsága, rendezése és CAlbumState kapcsolata nyitott. (3) ⛔ A PicasaPy forrása mappa- és nem üres albumkártyákat épít, de ugyanazon katalóguson futtatott teljes lista-összevetés és a RecentUpdate pontos tagsági szabálya hiányzik. (4) ⛔ A korábbi fejlesztési jegy #6713 a tulajdonosi átadás szerint létezik; ebből a helyi munkamenetből a státusza nem ellenőrizhető. A Recently Updated hiányát leíró pontos fejlesztői elfogadási feltételhez a bináris lista- és CAlbumState-híd még nem teljes; kiadási összehasonlító videó vagy képsor ebben a körben nem készült.

**Javasolt jegytörzs-bővítés.**

> A `docs/specs/picasa-idorend-bemutato-kutatas.md` 38.2.113 szakasza alapján a binárisban külön `CThumbDB::RecentUpdate` / `]updated` gyűjteményág van. A `0x0055ece0` ezen ágában a rekord descriptorának FILETIME értékét a jelenlegi idő mínusz 7 nap küszöbéhez hasonlítja, és a lista elemszámát a `RecentLimit` beállításhoz korlátozza, amelynek alapértéke 250. A job-239 futásban `Recently Updated (24)` látszott. A pontos FILETIME-esemény, a teljes tagsági és rendezési szabály, a CAlbumState `+0x0c == 2` sorral való kapcsolat és az ugyanazon katalóguson végzett PicasaPy-összehasonlítás **NINCS MEG**. E bizonyíték még nem ad pontos implementációs feladatlistát; ezeket a kérdéseket a #6532 kutatási elfogadási feltételei között kell tartani.

**Új kutatási jegyjavaslatok.** Nincs külön jegy; a nyitott pontok a #6532 részei.

**Nyitott.** A 2026-11-11-i Ghidra-kimenetek a függvények korábban hiányzó dekompilációit pótolták. A régi, általános célú kérések helyett az alábbi pontos kérdések maradnak:

- `Ghidra-kör kell: 0x004edf60 - melyik rekord és melyik adatforrás írja a descriptor +4/+8 mezőjét, és ezek a FILETIME szavak mely esemény dátumát jelentik [blokkoló]`. A `2026-11-11-6532-colab-decomp-7.txt` a két érték átmásolását mutatja, de az író és az esemény eredete nincs benne.
- `Ghidra-kör kell: 0x0055ece0 - mi a teljes elfogadási feltétel a hét napos ágon kívül, és milyen sorrendben áll a bemeneti param_2[2] tömb a RecentUpdate feldolgozásakor [blokkoló]`. A `2026-11-11-6532-colab-decomp-7.txt` igazolja a ciklust, a dátumkaput és a 0. pozícióra beszúrást, de nem azonosítja a tömb előállítóját, időrendi kulcsát és az összes külső előfeltételt.
- `Ghidra-kör kell: 0x004183c0 - a DBLoader vtable 0. helyén álló 0x0055ece0 függvényt mely regisztrált út hívja, és milyen adatbázis-esemény vagy életciklus indítja el [blokkoló]`. A `2026-11-11-6532-colab-decomp-7.txt` nem tartalmaz közvetlen kódhívót; a `2026-10-21-idorend-28.txt` és más találatok csak hívó/xref környezetben említik a címet, a függvény törzse nincs meg. A `.rdata` vtable és a `0x00402f90` konstruktor beállítása ismert, de az indirekt hívó és az ismétlési kiváltó nincs meg.
- `Ghidra-kör kell: 0x004b86d0 - a CAlbumState +0x138 rekord építésekor mely provider-bejegyzés vagy kulcs tartozik a ]updated kategóriához, és ez hogyan jut a +0x0c == 2 állapothoz [blokkoló]`. A `2026-10-21-idorend-21.txt` és `2026-11-11-6532-colab-decomp-7.txt` a `0x004b0190` általános provider-lekérdezését, a `0x004aae90` sorbejárását, a `0x004ab520` mezőírását, valamint a `0x004b8470` qshow-építő hívását mutatja, de `0x004b86d0` függvénytörzs nincs a Ghidra-kimenetek között; ez az új, konkrét sorépítő-kérdés ezért nyitott.
- A `0x004b3770` `Updated ` csoportosító és a `]updated` album közötti futásidejű lista-azonosság **NINCS MEG**. A `0x004b3770` eltérő köztes rekordot ír (`38.2.112`); a `Recently Updated` tagsága és azonos CAlbumState sora nincs megfigyelve.

**Módosított fájlok ebben a szakaszban.** A 38.2.113 a `Recently Updated` kulcs pozitív kódútját, a hét napos dátumfeltételt, a 250 elemű alapkorlátot és a fennmaradó tagsági/qshow kérdéseket rögzíti. Kódot, tesztet, videót, eredeti binárist vagy mérőadatot nem módosítottam.

#### 38.2.114 Recently Updated: a listaépítés és az Időrend-híd nyitott részei (#6532, 2026-11-11)

**Kérdés és eredmény.** A binárisból részben rekonstruálható a `CThumbDB::RecentUpdate` (`]updated`) frissítési útja, a dátumkapu, az elemek beszúrása és a korlát. Nem azonosítható, hogy a rekord FILETIME-ja fájlmódosítást, importot, szerkesztést, ini-írást vagy más eseményt jelöl-e. A teljes, emberi jelentésű tagsági szabály, a builder bemeneti sorrendje, a frissítés kiváltója, valamint a `]updated` kategória és a qshow `CAlbumState +0x0c == 2` sora közötti pontos kapcsolat továbbra is nyitott.

**Dátum és szűrés.** A `0x0055ece0` a `0x004edf60` által kitöltött descriptor `+4/+8` qwordját adja a `0x0098b650` konverternek, és a kapunál a `0x0098b770(7)` eredményéhez hasonlítja. A `0x0098b770` az aktuális `__time64` értékből hét darab 86400 másodperces napot von ki, majd Picasa-dátumértékké alakítja. A szigorú összehasonlítás csak a küszöbnél későbbi dátumot engedi át ezen az ágon. A `0x0055ece0` négy descriptor-típusnál (`0x15`, `0x17`, `0x18`, `0x1a`) nem végez dátumellenőrzést, és ezen a feldolgozási ágon nem is szúrja be az elemet a `]updated` listába (utasítások: `0x0055f057`-`0x0055f0cc`; részletesen 38.2.115). Ez nem a teljes tagság leírása. A rekordban tárolt két FILETIME-szó forrása és üzleti jelentése **NINCS MEG**.

**Bemenet, lista és sorrend.** A `0x0055ece0` a paraméterként kapott `param_2[2]` indexeit nullától növekvő sorrendben olvassa. A dátumkapun átjutó elemnél a `0x006c9e80` az ismétlődő azonosító korábbi példányát eltávolítja, majd az elemet a `]updated` vektor 0. pozíciójára teszi. E feldolgozási ág eredménye ezért a bemeneti bejárás fordított sorrendje, amíg a korlát csonkítása ezt meg nem változtatja. A `RecentLimit` alapértéke `0xfa`, vagyis 250 elem; a beállított érték felülírja az alapértéket, és a `0x006caf20` túllépéskor a vektor végétől töröl. E kódút önálló dátum szerinti rendezést nem végez. A `param_2[2]` előállítója és kezdeti sorrendje **NINCS MEG**.

A qshow külön útján a `0x007fc4c0` és a `0x0049cd60` a kártyák dátumkulcsait növekvő sorrendbe teszi. Ezt a `2026-11-11-6532-colab-decomp-4.txt` támasztja alá név szerint. Ez a qshow kártyasorrendje; nem bizonyítja, hogy a `]updated` lista ugyanezzel a kulccsal vagy sorrenddel készül, mert a két lista közötti rekordkapcsolat nincs meg.

**Regisztráció, frissítés és qshow-kapcsolat.** A `0x004a66e0` `FastStart == 0` ágából induló `0x004abe70` a `CThumbDB::RecentUpdate` megnevezés mellett a `0x004ad220` függvénynek adja át a `]updated` kulcsot. A `0x004ad220` a CAlbumState `+0xc4` providerében bejegyzést keres vagy hoz létre, és beállítja a `+0x166` jelzőt. Ez a kategória regisztrációját bizonyítja, nem azt, hogy mikor fut le a lista újraépítése.

A `0x0055ece0` a DBLoader vtable `0x00c7f5c0` 0. slotjában áll. A vtable-címet az objektumra beállító utasítás `0x004035f5`, a konstruktor `0x00402f90`, a konstruktor közvetlen hívója `0x004051b0`. A vtable útból nem állapítható meg, melyik adatbázis-esemény vagy életciklus hívja meg a slotot, milyen gyakran frissül a lista, vagy milyen feltétel után.

A külön CAlbumState-frissítő útban a `0x004afcb0` meghívja a `0x004aae90` függvényt; ez a `0x004b0190` provider-lekérdezésen át sorokat jár be, majd egyes ágakban a `0x004ab520` segítségével `2`-t ír a `+0x0c` mezőbe. A qshow `0x004b29d0` útja ilyen `+0x0c == 2` forrássort fogyaszt. A már meglévő `0x004b0190` dekompiláció a virtuális provider-lekérdezést mutatja, de nem bizonyítja, hogy a `]updated` kulcs melyik CAlbumState-indexhez tartozik. E két út összekötése és a frissítést kiváltó esemény **NINCS MEG**.

**PicasaPy-összevetés.** A `src/picasapy/app/timeline_controller.py` `_collections_to_qml()` útja mappákból és átadott, nem üres normál albumokból állítja össze a kártyákat; a dátumot az EXIF szerinti felvételi időből kéri. A `src/picasapy/index/albums.py` ini-albumdefiníciókat olvas. A forrásban nincs külön `Recently Updated`, `RecentUpdate` vagy `]updated` ág. Ez alátámasztja, hogy a PicasaPy-ban nincs külön dinamikus albumépítő, de a két alkalmazás azonos képhalmazon vett tagsága nem hasonlítható össze, amíg az eredeti FILETIME mező jelentése és teljes tagsági szabálya ismeretlen.

| Állítás | Bizonyíték |
|---|---|
| A dátumküszöb az aktuális időből hét nap levonásával képződik, és a vizsgált ág szigorúan későbbi dátumot fogad el. | bináris (`0x0055ece0`, `0x0098b770`, `0x0098b650`, `0x00c0a421`) |
| A dátumteszt alól kivett descriptor-típusok `0x15`, `0x17`, `0x18`, `0x1a`. | bináris (`0x0055ece0`, `0x004edf60`) |
| A descriptor `+4/+8` FILETIME mezőjét a `0x004edf60` adja tovább; az esemény, amelynek ideje bekerül, ismeretlen. | bináris (`0x004edf60`, `0x0055ece0`, `0x0098b650`); eseményjelentés: NINCS MEG |
| A bemeneti indexbejárás növekvő, az elfogadott elemeket a 0. pozícióra szúrja, ismétlődést eltávolít, a végéből vág. | bináris (`0x0055ece0`, `0x006c9e80`, `0x006caf20`) |
| A `RecentLimit` alapértéke 250, felhasználói beállítás felülírhatja. | bináris (`0x0055ece0`, `0x0055f0db`, `0x0055f101`, `0x006caf20`) |
| A qshow kártyái növekvő dátumkulccsal rendeződnek, ez nem bizonyíték a `]updated` lista sorrendjére. | bináris (`2026-11-11-6532-colab-decomp-4.txt`, `0x007fc4c0`, `0x0049cd60`) |
| A `]updated` kategória a `CThumbDB::RecentUpdate` címke alatt kerül a providerbe. | bináris (`0x004abe70`, `0x004ad220`) |
| A `0x004aae90` egyes CAlbumState-sorokra `+0x0c == 2` értéket állít, a `0x004b29d0` ezt fogyasztja. | bináris (`0x004aae90`, `0x004ab520`, `0x004b0190`, `0x004b29d0`) |
| A `]updated` kulcsot hordozó CAlbumState-index és az Időrendbe jutó qshow-sor azonossága. | NINCS MEG |
| A rekord FILETIME mezőjének eseményjelentése, a builder bemeneti tömbjének előállítója és kezdeti sorrendje. | NINCS MEG |
| Az adatbázis-esemény, amely a DBLoader vtable 0. slotját meghívja, valamint az ismétlődő frissítés ütemezése. | NINCS MEG |
| PicasaPy külön dinamikus `Recently Updated` builderének hiánya. | mérés (forrásleolvasás: `src/picasapy/app/timeline_controller.py`, `src/picasapy/index/albums.py`; a tokenekre végzett `rg` keresés üres) |
| Egy korábbi Picasa futásban a `Recently Updated` címke és a 24-es elemszám látszott. | mérés (`job-239/kepernyo__02.png`, 38.2.81) |
| Az eredeti Picasa Időrendről készült videó dokumentálva van. | mérés (job-373 és job-446, 38.2.101 és 38.2.104) |

**A két független út.** A út: a Ghidra-kimenetek (`2026-11-11-6532-colab-decomp-7.txt`, `2026-11-11-6532-colab-updated-hivok.txt`, `2026-11-11-6532-colab-decomp-3.txt`, `2026-11-11-6532-colab-decomp-5.txt`) a FILETIME tesztet, a provider-regisztrációt, a pozíció 0 beszúrást és az általános `+0x0c == 2` frissítést mutatják. B út: a helyi utasításolvasás, a `paszta.py`-val kapuzott vtable-címkeresés, a PE `.rdata` leolvasás és az SQLite pozitív xrefjei külön ellenőrzik a vtable 0. slotját, a `0x0098b770` hétnapos kivonását és az insert/limit segédek viselkedését. A második kontextusú levezetés ugyanezt találta a dátumkapuról, a nulladik pozícióra beszúrásról és a korlátról. A két út egyezik ezekben a részállításokban; egyik sem bizonyítja az időbélyeg eseményét vagy a qshow-sor pontos azonosságát.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a `]updated` kimeneti lista sorrendje a qshow növekvő dátumrendezése. A `2026-11-11-6532-colab-decomp-4.txt` a qshow dátumkulcs-rendezését mutatja a `0x007fc4c0` és `0x0049cd60` útján; a `2026-11-11-6532-colab-decomp-7.txt` a Recently Updated elemek bemeneti index szerinti bejárását és 0. pozícióra szúrását írja le. A két kódrész külön listán dolgozik, ezért az azonos sorrendre vonatkozó állítás nem következik belőlük. Azt is ellenőriztem, hogy a `CAlbumBuilder::updated` azonos-e a `]updated` albummal: a külön köztes rekord `+0x30 == 2`, míg a qshow út `+0x30 == 1` értéket követel (`38.2.112`); az azonosítást ez a mezőfeltétel cáfolja.

**Bizonyítottsági fok.** A dátumkapu, a kivétellista, a lista elejére szúrás és a `RecentLimit` alapértéke két független úton megerősített. A `Recently Updated` teljes viselkedése **nyitott**, mert a timestamp eredete, a teljes tagsági szabály üzleti értelmezése, a builder bemeneti sorrendje, a frissítés kiváltója és a CAlbumState/qshow kapcsolat nincs lezárva.

**A #6532 „Kész, ha” pontjai.** (1) ✅ Eredeti videó áll rendelkezésre a korábban rögzített job-373 és job-446 felvételekből (`38.2.101`, `38.2.104`); ebben a körben új felvétel nem készült. (2) ⛔ A spec több binárisból igazolt részt tartalmaz, de a FILETIME üzleti jelentése, a teljes tagság, a frissítési kiváltó és az Időrend-sor azonossága nyitott. (3) ⛔ A PicasaPy külön `Recently Updated` útja hiányzik, de azonos katalóguson végzett, tagság szerinti összevetéshez a nyitott eredeti szabályok kellenek. (4) ⛔ Nem születik fejlesztési jegytörzs, mert az eredeti dátumforrás és tagság nélkül az implementációhoz kitalált szemantika kellene; összehasonlító kiadási videó vagy képsor ebben a körben nem készült.

**Javasolt jegytörzs-bővítés.** A #6532-ben ezt a kutatási állapotot érdemes rögzíteni: a bináris `CThumbDB::RecentUpdate` / `]updated` ága a descriptor FILETIME-ját a jelenlegi idő mínusz hét nap küszöbhöz hasonlítja, négy descriptor-kódnál kihagyja ezt a dátumtesztet, majd a bemeneti indexek feldolgozási sorrendjét megfordítja a lista elejére szúrással. A `RecentLimit` alapértéke 250. A PicasaPy forrásában nincs külön dinamikus `Recently Updated` builder. A descriptor idejének eseményjelentése, a teljes albumtagság, a frissítést kiváltó adatbázis-esemény és a CAlbumState/qshow kapcsolat **NINCS MEG**, ezért ebből a bizonyítékból még nem adható biztonságosan végrehajtható fejlesztési teendőlista.

**Új kutatási jegyjavaslatok.** Nincs külön jegyjavaslat; a nyitott pontok a #6532 elfogadási feltételei.

**Nyitott.**

- `Ghidra-kör kell: 0x004edf60: mely kód írja a descriptor +4/+8 szavainak forrásrekordját, és az időérték mely eseményt jelenti [blokkoló]`. A `2026-11-11-6532-colab-decomp-7.txt` már megmutatja, hogy a `0x004edf60` a forrásrekord két szavát továbbadja; ezt a kimenetet a forrásrekord írójának és eseményjelentésének kérdése nem válaszolja meg.
- `Ghidra-kör kell: 0x0055ece0: mely kód állítja elő a param_2[2] bemeneti tömböt és annak sorrendjét, és mely nem-dátum feltételek határozzák meg a felvételt [blokkoló]`. A `2026-11-11-6532-colab-decomp-7.txt` a fogyasztói ciklust és a dátumkaput tartalmazza, de nem nevezi meg a tömb előállítóját vagy időrendi kulcsát.
- `Ghidra-kör kell: 0x004183c0: ki és milyen adatbázis-esemény vagy életciklus során hívja meg a DBLoader vtable 0. slotját [blokkoló]`. Az előző kimenetekben ez a cím csak hívó/xref környezetben szerepel; a függvény törzse nem található meg, és a `0x0055ece0` vtable-dispatch útvonalának kiváltója nyitott.
- `Ghidra-kör kell: 0x004b86d0: a CAlbumState +0x138 rekord építésekor mely provider-bejegyzés vagy kulcs tartozik a ]updated kategóriához, és ez hogyan jut a +0x0c == 2 állapothoz [blokkoló]`. A meglévő `2026-10-21-idorend-21.txt` és `2026-11-11-6532-colab-decomp-7.txt` a `0x004b0190` általános provider-lekérdezését, a `0x004aae90` sorbejárását, a `0x004ab520` mezőírását, valamint a `0x004b8470` qshow-építő hívását mutatja, de `0x004b86d0` függvénytörzs nincs a Ghidra-kimenetek között; ez az új, konkrét sorépítő-kérdés ezért nyitott.

**Módosított fájlok ebben a szakaszban.** A 38.2.114 kiegészíti a 38.2.113 leleteit a lista sorrendjével, a decomp-4 kötelező hivatkozásával, a vtable és provider út elválasztásával, a PicasaPy összevetéssel és a nyitott kutatási kérdésekkel. Kódot, tesztet, videót, eredeti binárist vagy mérőadatot nem módosítottam.


#### 38.2.115 Recently Updated: DBLoader-regisztráció és a kizárt típusok (#6532, 2026-11-11)

**Forrás és hatókör.** A `~/picasapy-agent/referencia/ghidra/2026-11-11-6532-colab-decomp-9.txt` és a `~/picasapy-agent/referencia/ghidra/2026-11-11-6532-colab-9-hivok.txt` új dekompilációi, a `2026-11-11-6532-colab-decomp-7.txt` és az eredeti, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96` azonosítójú bináris célzott utasításai.

**DBLoader: a közvetlen hívó és regisztráció.** A `0x00402f90` a `0x004035f5` címen a `0x00c7f5c0` vtáblát állítja be; a slotja `0x0055ece0`. Ugyanez az objektummutató a `0x00403614`-`0x0040361c` utasításokkal argumentumként kerül a közvetlenül hívott `0x004183c0`-hoz. Utóbbi a `CThumbDB+0xf8` objektumot készíti elő, majd az argumentumot a `0x004188cf` címen átadja a `0x004e4ea0`-nak. A `0x004e4ea0` nem nulla argumentum esetén, ha a lista jelzőjének 0. bitje nulla és a tárolás sikerül, a mutatót a `+0x484` listához fűzi (`0x004e4ebc`-`0x004e4f77`), majd az inicializálást folytatja. Ez regisztrációs út, **nem bizonyítja** a slot meghívásának időpontját, gyakoriságát vagy eseményét. A korábbi 38.2.114 kérdésében szereplő `0x004183c0` nem a `0x0055ece0` közvetett hívójaként igazolt: önálló inicializáló, melynek közvetlen hívója a konstruktor.

**A négy típus kizárása ezen az ágon.** A `0x0055f057` nullázza a `BL` jelzőt; a `0x0055f07f`-`0x0055f091` összehasonlításai a `0x15`, `0x18`, `0x17`, `0x1a` típusnál a jelző beállításán túlra ugranak. A `0x0055f0ca`-`0x0055f0cc` nullánál átugorja a `]updated` lookupot és a `0x006c9e80` beszúrást. Más típusnál a szigorú időösszehasonlítás állíthatja be a jelzőt (`0x0055f093`-`0x0055f0bd`). A decomp-7 `bVar2 = false` és `if (bVar2)` ága ezt külön is alátámasztja. A típusok emberi jelentése és az esetleges egyéb listaíró utak **NINCS MEG**; a fenti kizárás kizárólag a vizsgált beszúrási ágra vonatkozik.

**A CAlbumState-sor.** A `0x004b8ee0` a nem nulla `+0x0c` mezőjű sor indexével hívja a `0x004b86d0`-t (`0x004b90cb`). Az utóbbi a `0x00448c90` eredményétől függően a `0x004b5fa0` vagy `0x004b6090` eredményét a `+0x428` indexelt tömbbe írja, a második ágon a `+0x438` tömbbe is. A hívók dekompilációjában mindkét segéd a `0x004b0190` provider-lekérdezést használja, és rendre a `0x006cb820` vagy `0x006cb890` eredményéből dolgozik. Ez azonosítja a vizsgált sorfeldolgozást, de **nem** bizonyítja, hogy a sor a `]updated` kulcsé vagy `+0x0c == 2` értékű. A figyelmeztetéseket tartalmazó Ghidra-kimenet nem alkalmas önmagában valamennyi ág kizárására.

**Bizonyítottság és cáfolat.** A regisztráció és a négy típus fenti ágbeli kizárása **megerősített**: A út a Ghidra C-kimenete és a hívókapcsolat; B út a helyi gépi utasítások külön olvasása (`0x004035f5`, `0x00418892`, `0x004e4ebc`, `0x0055f057`). Egyeznek. Cáfoló feltevés: a négy típus dátumteszt nélkül bekerül a listába. A `BL=0` → típusugrás → `test bl` → beszúrás átugrása út és az önálló dekompilált `bVar2` vezérlés egyaránt cáfolja a vizsgált ágon. A teljes album viselkedése **nyitott**.

| Állítás | Forrás |
|---|---|
| DBLoader-mutató átadása és feltételes hozzáfűzése | bináris (`0x004035f5`, `0x0040361c`, `0x004188cf`, `0x004e4f61`) |
| Négy típus nem jut el az itt vizsgált beszúráshoz | bináris (`0x0055f057`, `0x0055f07f`-`0x0055f0cc`) |
| A descriptor forrásrekordjának `+4/+8` szavai és a dátumot adó esemény | NINCS MEG |
| A `param_2[2]` tömb előállítója, sorrendje, teljes tagsági feltétel | NINCS MEG |
| A regisztrált objektum 0. slotját meghívó út és esemény | NINCS MEG |
| A `]updated` és az Időrend `+0x0c == 2` sora közötti azonosság | NINCS MEG |

**További célok.** A célzott helyi diszasszemblálás és a meglévő dekompilátumok nem döntik el a hiányzó szemantikát. Teljes `.text` pásztázás nem futott: a külső `systemd` memóriakorlát létrehozását a környezet megtagadta; az index negatív találatát nem használjuk bizonyítékként.

- `Ghidra-kör kell: 0x004edf60, melyik kód írja a forrásrekord +4/+8 szavait és milyen esemény időpontja kerül oda [blokkoló]`. A decomp-7 csak az átmásolást mutatja.
- `Ghidra-kör kell: 0x0055ece0, ki állítja elő a param_2[2] tömböt, milyen sorrendben és mely nem-dátum feltételekkel [blokkoló]`. A decomp-7 a fogyasztót mutatja, az előállítót nem.
- `Ghidra-kör kell: 0x004e4ea0, a +0x484 listába regisztrált DBLoader objektumot melyik út veszi ki és hívja a 0. slotján, milyen eseménnyel és paraméterrel [blokkoló]`. A 0x004e4ea0 lokális utasításai a regisztrációt, nem a dispatch-et mutatják.
- `Ghidra-kör kell: 0x004aae90, a ]updated providerazonosító melyik sorba kerül, és milyen feltétellel lesz a sor +0x0c mezője 2 [blokkoló]`. A meglévő dekompiláció az általános sorbejárást mutatja, a kulcs konkrét sorhoz kötését nem; a 0x004b86d0 új kimenete az indexelt segédértékeket, nem ezt az azonosságot mutatja.

**A #6532 készültsége.** A korábbi eredeti videók dokumentáltak (38.2.101, 38.2.104). A teljes spec, a tételes azonos mintás összevetés és az új, pontos fejlesztési jegy feltételei a fenti hiányok miatt nem teljesülnek; a korábban megnyitott #6713 a 38.2.102-ben azonosított eltérésekre vonatkozik. A Recently Updated teljes fejlesztési feladatlistája nem vezethető le biztonsággal.

#### 38.2.116 Recently Updated: a bemeneti kapuk és a sorállapot átmenete (#6532, 2026-11-11)

**Forrás.** `~/picasapy-agent/referencia/ghidra/2026-11-11-6532-colab-decomp-10.txt` és `~/picasapy-agent/referencia/ghidra/2026-11-11-6532-colab-10-iro-es-hivok.txt`; az eredeti 3.9.141.259 bináris SHA-256 értéke `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. Az utasításokat helyi célzott diszasszembly is ellenőrizte. A hívókat tartalmazó fájl 109 dekompilált hívót sorol fel; közöttük a `0x0055ece0` tartalmazza a `]updated` ágat. Ez fogyasztó, a rekordidő eredetét önmagában nem bizonyítja.

**A feldolgozás további kapui.** A `0x0055ece0` csak a `0x005608f0` nulla visszatérése után folytatja a vizsgált utat (`0x0055ed38`-`0x0055ed3f`), és a bemeneti elemszám (`param_2[3] >> 1`) nem lehet nulla (`0x0055ed59`-`0x0055ed6c`). A `0x004e39c0(param_2[1])` eredményének `+0x18` mezője `1` vagy `0x19` kell legyen (`0x0055ed88`-`0x0055ed98`). A beszúrás előtti úton a `0x00425f60` nulla visszatérése is feltétel; ha `param_2` `+0x29` bájtja nulla, előbb a `0x00456610` nulla visszatérése is kell (`0x0055eedc`-`0x0055ef1c`). Ezek bináris kapuk, nem a teljes albumtagság szemantikus definíciói. A `param_2[2]` előállítója és sorrendje **NINCS MEG**.

**A sorfrissítő ága.** A `0x004aae90` a sor `+0x0c` mezőjére egymás után két feltételt alkalmaz: az első `1` vagy `2`, a második `3` vagy `1` értéket enged (`0x004ab31d`-`0x004ab33b`). Metszetük kizárólag `1`. Az ilyen sor indexével hívott `0x004b0190` nulla visszatérése után a két ágon `2` argumentummal hívja a `0x004ab520`-at (`0x004ab359`-`0x004ab360`, `0x004ab45f`-`0x004ab46b`, `0x004ab494`-`0x004ab49b`); utóbbi az indexelt `+0x0c` mezőbe ír (`0x004ab570`-`0x004ab57d`). A `]updated` kulcs konkrét sorhoz kötése **NINCS MEG**, ezért ez az átmenet nem bizonyítja, hogy a kérdéses album sora átmegy rajta.

**A hívás feltétele, nem az eredeti esemény.** A `0x004afcb0` a `0x004a8a30` után akkor jut a `0x004aae90` hívásáig, ha a `+0x166` vagy a `+0x161` bájt nem nulla (`0x004afcfd`-`0x004afd1a`). A jelzőket kiváltó esemény és a DBLoader 0. slotját meghívó út **NINCS MEG**; a sorfrissítő és a DBLoader diszpécselése külön kérdés.

**Cáfoló kísérlet.** Feltevés: a `2` állapotú sor közvetlenül eljut a `0x004aae90` 2-t író ágához. A dekompilátum két egymásba ágyazott feltétele, és ettől külön a gépi `cmp`/ugrás lánc is cáfolja: az első kapun átjutó `2` a másodikon kiesik. A cáfolatot a külön `0x004ab520` író utasításai is ellenőrzik: valóban a vizsgált sor `+0x0c` mezőjét írja. Ez a kizárás csak e függvény adott útjára vonatkozik. Másik ellenőrzés: a `0x00503920` dekompilátumban a rekordtömbön talált `piVar19[3]` és `[4]` írás `+0x0c` és `+0x10`, nem a `0x004ee08a`-`0x004ee093` által másolt `+4/+8`, tehát nem bizonyítja a keresett dátum forrását.

| Állítás | Forrás | Fok |
|---|---|---|
| A sor állapota az itt vizsgált 2-re állító úton előzőleg 1 | bináris (`0x004ab31d`-`0x004ab33b`, `0x004ab359`, `0x004ab46b`, `0x004ab49b`, `0x004ab57d`) | megerősített: vezérlés és külön mezőíró |
| A `0x004afcb0` sorfrissítési hívása jelzőkhöz kötött | bináris (`0x004afcfd`-`0x004afd1a`) | megerősített: hívó utasításai és a meghívott függvény jelzőkezelése (`0x004aae90`) |
| A `]updated` bemeneti és feldolgozási kapui | bináris (`0x0055ed38`-`0x0055ed98`, `0x0055eedc`-`0x0055ef1c`, `0x0055f074`) | megerősített: hívási út és külön gépi utasítások |
| A dátumot létrehozó esemény, a bemeneti tömb előállítója és sorrendje, a DBLoader dispatch, a `]updated` sorazonossága | NINCS MEG | nyitott |

A teljes `.text` pásztázás nem futott: a szükséges külső `systemd` memóriakorlát létrehozását a környezet megtagadta. Az index negatív találata nem bizonyíték. A meglévő kimeneteket az alábbi címekre előzetesen ellenőriztük; az új kérdések a meglévő törzsek által nem megválaszolt adatfolyamra vonatkoznak.

- `Ghidra-kör kell: 0x004edf60 - a +0x3f0 rekordtömb kiválasztott rekordjának +4/+8 írója és az oda kerülő idő eseménye; a meglévő kimenet csak a másolást mutatja [blokkoló]`
- `Ghidra-kör kell: 0x0055ece0 - a param_2[2] tömböt előállító és rendező út, valamint a 0x00425f60 és 0x00456610 kapuk jelentése; a meglévő kimenet a fogyasztóoldalt mutatja [blokkoló]`
- `Ghidra-kör kell: 0x004e4ea0 - a +0x484 listában regisztrált objektum 0. slotjának tényleges indirekt hívója, argumentuma és kiváltó eseménye; a meglévő kimenet a regisztrációt mutatja [blokkoló]`
- `Ghidra-kör kell: 0x004aae90 - a ]updated providerazonosítót a konkrét sorindexhez kötő út és az 1-es előállásának feltétele; a meglévő kimenet az általános 1-ről 2-re váltást mutatja [blokkoló]`

A korábban dokumentált eredeti videók és a #6713 megvalósítási jegy léte változatlan (38.2.101, 38.2.104, 38.2.102). A teljes bináris bizonyítás és az azonos mintás tételes összevetés nem teljes; ebből a körből teljes Recently Updated fejlesztési jegy nem vezethető le.

#### 38.2.117 A dátumot adó rekord kiválasztásának feltételes átirányítása (#6532, 2026-11-11)

A 38.2.114 `0x004edf60` rekordolvasójában a `+4/+8` szavak forrása nem minden esetben a közvetlenül indexelt rekord. A `0x004edfaf`-`0x004edfe0` a `+0x3f0` mutatótömbből választ; nulla mutatónál az objektum `+0x3f8` alaprekordjára esik vissza. Ha a kiválasztott rekord `+0x18` dwordja `0x3e9`, és a `+0x20` indexe nem `0xffffffff`, valamint kisebb a `+0x3f4 >> 1` elemszámnál, a `0x004edfe2`-`0x004ee01b` ugyanebből a tömbből a célrekordot választja ki, null mutatónál ismét az alaprekordot. A `0x004ee08a`-`0x004ee093` az így kiválasztott rekord `+4/+8` szavait másolja a kimenetbe. Az átirányítás ellenőrzése ezen az úton egyszer történik; ez nem bizonyít tetszőleges hosszúságú lánckövetést. A rekordtípus emberi jelentése **NINCS MEG**.

Ha a célindex `0xffffffff` vagy kívül esik a tartományon, az eredeti kiválasztás marad. Ha a végül kiválasztott rekord `+0x18` értéke nulla, a `0x004ee02a`-`0x004ee02d` a `+4/+8` másolását kihagyó ágra ugrik (`0x004ee0cc`); ez az ág ezeket a kimeneti mezőket nem állítja be. Ez a megállapítás a másolásig tartó út és az adott ág leírása: a `0x004ee0e7` utáni további feldolgozás külön vizsgálandó.

**Bizonyítottság: megerősített** a fenti feltételes kiválasztásra. A út: a `2026-11-11-6532-colab-decomp-10.txt` `FUN_004edf60` kimenete; B út: a helyi bináris független, utasításonkénti olvasása (`0x004edfe2`-`0x004ee01b`, `0x004ee02a`-`0x004ee02d`, `0x004ee08a`-`0x004ee093`, `0x004ee0cc`-`0x004ee0e1`). A két olvasat egyezik. **Cáfoló próba:** az érvénytelen célindexre is átirányítást feltételezve az `0xffffffff`-összehasonlítás és a határellenőrzés ugrásait, valamint külön a dekompilált feltételeket vizsgáltuk; mindkettő az eredeti kiválasztást tartja meg. A további `0x004ee0e7` utáni ágat külön ellenőrizve a következtetés csak a fent megjelölt rekordválasztásra korlátozódik.

| Állítás | Forrás |
|---|---|
| A `0x3e9` típus érvényes `+0x20` célindex esetén másik forrásrekordot választ a `+4/+8` másolásához. | bináris (`0x004edfe2`-`0x004ee01b`, `0x004ee08a`-`0x004ee093`) |
| Nulla `+0x18` mellett a szavak másolása ezen az ágon elmarad. | bináris (`0x004ee02a`-`0x004ee02d`, `0x004ee0cc`-`0x004ee0e1`) |
| A `+4/+8` szavak írója és időpontjának eseményjelentése, a `0x3e9` típus felhasználói jelentése. | NINCS MEG |

A `]updated` út tényleges bemenetein az átirányítás előfordulása és az időbélyeg eredete nem igazolt; ebből önmagában PicasaPy-eltérés vagy fejlesztési feladat nem következik. A 38.2.116 nyitott Ghidra-kérdései érvényesek, az időbélyeg íróját a közvetlen és az esetleg átirányított rekordra egyaránt keresni kell.

**Kiegészítés: a keresett FILETIME rekordmezője és írói.** A fenti táblázat íróra vonatkozó `NINCS MEG` sora részben feloldható. A `0x004edf60` által másolt első FILETIME a `thumbindex.db` rekord első időmezője (`pmp-database.md` 10.3 és 15.1); ez nem azonos a második, aktuális fájlmódosítási időt tároló mezővel. A `0x004eeb10` ugyanazon `+0x3f0` mutatótömb indexelt rekordjának `+4` címére írja a konvertált értéket (`0x004eeb6d`, `0x004eeba4`, `0x004eebad`). A `0x00425f60` a `0x00427844` címen a `0x37` metaadatkulcsot kéri, és sikeres olvasás és dátumkonverzió után a `0x00427898` címen hívja az írót. A kulcs az EXIF `DateTimeOriginal` mezője (`picasa-metaadat-tulajdonsagok.md` 3., `0x00c788d8`). A mező tehát ebben az esetben a felvétel metaadat-dátuma, nem a kép első indexelésének időpontja. A `0x004ef3c0` és `0x004ef5a0` dátumállító utak ugyanezt az első mezőt módosíthatják (`pmp-database.md` 15.1; `0x004ef666`, `0x004ef66e`), ezért az érték nem feltétlenül marad örökre változatlan.

**Kezdőérték: feltárt rekordépítő út, korlátozott következtetés.** A `0x004e753f` és `0x004e7545` a bejáró `WIN32_FIND_DATAA` szerkezetéből a `ftLastWriteTime` két szavát tölti, a `0x004e756a` átadja a `0x0040f980` rekordépítőnek. Ez a két szót az első és a második FILETIME-ba egyaránt beírja (`0x0040f9b6`-`0x0040f9db`); a `0x004e7689` a képzett rekordot egy rekordtömbbe másolja. A két időmező egyezését korábbi katalógusmérés is vizsgálta (`pmp-database.md` 10.4). Az itt feltárt útból még nem következik, hogy az adott `]updated` bemenet minden metaadat nélküli rekordja ezen az úton kerül a getter tárolójába: a teljes kapcsolat és az esetleges más írók **NINCS MEG**. Így az első mező nem nevezhető általánosan sem aktuális fájlmódosítási időnek, sem minden esetben kizárólag EXIF-időnek.

**Mérés és cáfolat.** A job-545 és job-547 képein mindkét gyűjtemény 24 képet jelez; a mappában első szürke átmenet az album 21., a második színtábla a 24. eleme. Ez cáfolja, hogy a két megjelenített lista azonos sorrendű volna; önmagában nem azonosítja az album rendezési kulcsát. A job-551 beszámoló szerint forgatás, lemezre mentés és újraindítás után a szürke átmenet helye változatlan maradt. Az, hogy a mentés valóban megváltoztatta-e a fájl módosítási idejét, nincs mérve, ezért e próba önmagában nem zárja ki annak szerepét. A binárisban az első és második FILETIME külön mező (`0x004ee08a`, `0x004ee09c`), és a friss fájlidőt a vizsgált frissítési út a másodikba írja (`0x004e74dc`, `0x004e74df`); ez külön ellenőrzi a cáfolat korlátját.

| Állítás | Forrás | Fok |
|---|---|---|
| Az olvasott első FILETIME érvényes metaadat esetén a `DateTimeOriginal` értékéből is íródik. | bináris (`0x00427844`, `0x00427898`, `0x004eeb6d`, `0x004eebad`, `0x00c788d8`) | megerősített: írói adatfolyam és független metaadatkulcs-tábla |
| A vizsgált rekordépítő a fájl módosítási idejét mindkét időmezőbe bemásolja. | bináris (`0x004e753f`, `0x004e756a`, `0x0040f9b6`, `0x0040f9db`); mérés (`pmp-database.md` 10.4) | megerősített erre az építőútra |
| A `]updated` teljes bemeneti sorrendje és a metaadat nélküli rekord végleges útja. | NINCS MEG | nyitott |

A meglévő dekompilátumok ellenőrzése után a korábbi kérdés pontosítható:

- `Ghidra-kör kell: 0x004e62d0 - a 0x004e753b által épített rekordtömb útja a 0x004edf60 +0x3f0 tárolójába és a metaadat nélküli rekord kezdeti értékének megőrzése [blokkoló]`. A rendelkezésre álló kimenetek csak hívóként említik, a törzse nincs meg.
- `Ghidra-kör kell: 0x0055ece0 - a param_2[2] előállítója és sorrendje, valamint a nem dátum jellegű kapuk jelentése [blokkoló]`. A meglévő dekompilátum a fogyasztót mutatja, az előállítót nem.
- `Ghidra-kör kell: 0x004e4ea0 - a regisztrált DBLoader 0. slotjának tényleges hívója, argumentuma és kiváltó eseménye [blokkoló]`. A meglévő kimenet a regisztrációt mutatja.

A teljes tagság és sorrend továbbra sincs igazolva, ezért a Recently Updated teljes megvalósítására kész fejlesztői jegy ebből még nem vezethető le.


#### 38.2.119 Recently Updated: időküszöb, videótípusok és a listaállapot határa (#6532, 2026-11-11)

**Hatókör és fok.** Az időküszöb és a mért videótípusok kizárási tesztje két külön úton alátámasztott; a beszúró belső működése **feltételes**, mert a dekompilátum és a gépi kód ugyanazon kódutat olvassa. A teljes tagság és a megjelenített sorrend **nyitott**. A munkafa e kör elején a 38.2.117 szakaszig tartott; külön 38.2.118 szakasz itt nem volt.

**Időküszöb.** A `0x0055f0a1` a `7` argumentumot adja, a `0x0098b77e` az aktuális `__time64` értéket kéri, a `0x0098b783`-`0x0098b790` pedig abból `7 * 0x15180 = 604800` másodpercet von ki. A `0x0098b7b4` helyi naptári időre alakítja a küszöböt, amelyet a `0x0098b550` kódol. A rekord `FILETIME` értékét a `0x0098b650` a `FileTimeToSystemTime`, `SystemTimeToTzSpecificLocalTime`, `SystemTimeToVariantTime` importokon keresztül helyi naptári értékké alakítja (`0x0098b675`, `0x0098b68b`, `0x0098b69a`). A `0x0055f0b1`-`0x0055f0bd` ezeket hasonlítja össze. A kivonás időtartama tehát igazolt, de a 38.2.113 korábbi, minden körülményre pontos eltelt másodperces ablakként tett állítása túl erős: az összehasonlítás helyi időértékeken történik. Időzóna- és óraátállítási peremteszt **NINCS MEG**.

**Videók és kizárt típusok.** A `0x004ee0a8`-`0x004ee0ab` a kiválasztott rekord `+0x18` típusát a descriptor azonos mezőjébe másolja; a kiválasztás a 38.2.117 szerinti átirányítást is alkalmazhatja. A `0x0055f07f`-`0x0055f091` a `0x15`, `0x17`, `0x18`, `0x1a` kódokra átugorja a dátumtesztet, majd a nulla jelző miatt a `0x0055f0ca`-`0x0055f0cc` nem indítja az itt vizsgált beszúrást. A `pmp-database.md` 15.1 korábbi katalógusmérése az `.avi` videóknál 8, az `.mp4`, `.mpg`, `.mts` videóknál 10, a `.wmv` videóknál 11 típust rögzített. E mért kódok nem tartoznak a négy kizárt szám közé. Ebből **nem következik**, hogy minden videó felvételt nyer: a többi kapu, a rekordválasztás és a teljes listaíró út is számít. Más fájltípusok teljes tagsága **NINCS MEG**.

**Sorrend és cáfolat.** A `0x0055ece0` a bemeneti tömb elemeit növekvő tömbindex szerint olvassa, és a `0x0055f149`-`0x0055f157` sikeres úton 0 pozícióval és 1-es jelzővel hívja a `0x006c9e80` beszúrót. A beszúró e jelző mellett előbb keresi az azonos értéket (`0x006c9ee8`, a kereső `0x005b3415`), majd találat és módosítható, nem üres tároló esetén az első találatot eltávolítja (`0x006c9ef0`-`0x006c9f28`), mielőtt a `0x008e5120` beszúrást hívná (`0x006ca06c`-`0x006ca077`). A `0x0055f162`-`0x0055f191` a korlát feletti utolsó elemeket eltávolítja. **Cáfoló feltevés:** a végső lista minden körülmény között a bemenet egyszerű megfordítása. Az előzetes listában megtalált elem eltávolítása és az előzetes lista léte ezt a feltétel nélküli állítást nem engedi; a keresést és az eltávolítást a dekompilátum és a gépi kód külön ellenőrzi. A 24 képes mérésből csak két pozíció ismert, a bemeneti azonosítósorrend **NINCS MEG**, így a fordított indexelési sorrenddel összevetés sem végezhető el.

**Két független út.** A: a meglévő `2026-11-11-6532-colab-decomp-7.txt` és `2026-11-11-6532-colab-decomp-9.txt` vezérlési és listaolvasata. B: a célzott helyi utasításolvasás a fenti címeken, a PE importtáblájának API-neveivel; a videótípusokhoz ettől külön a `pmp-database.md` 15.1 katalogizált mérése. A leírt részek egyeznek, de ugyanazon függvény dekompilálása és gépi kódja önmagában nem két független végrehajtási út: a beszúró belső viselkedése ezért feltételes. Az importtábla és a hívó, illetve a külön katalógusmérés más forrásból támasztja alá az idő- és típusleletet. A videók tényleges felvétele és a végső sorrend tekintetében a két út nem ad teljes választ.

| Állítás | Forrás |
|---|---|
| Küszöbképzés: aktuális idő mínusz `604800` másodperc | bináris (`0x0055f0a1`, `0x0098b77e`, `0x0098b783`-`0x0098b790`) |
| Összehasonlítás helyi naptári reprezentációban | bináris (`0x0098b675`, `0x0098b68b`, `0x0098b69a`, `0x0098b7b4`, `0x0055f0b1`) |
| Négy kizárt típus a vizsgált ágon | bináris (`0x0055f07f`-`0x0055f091`, `0x0055f0ca`) |
| Példakatalógusban videók típusa 8, 10, 11 | mérés (`pmp-database.md` 15.1) |
| Meglévő elem feltételes előzetes eltávolítása | bináris (`0x006c9ee8`-`0x006c9f28`, `0x005b3415`) |
| A bemeneti tömb építője, sorrendje, a teljes tagság és a 24 elem összevethető indexsorrendje | NINCS MEG |

**Következő célzott vizsgálat.** `Ghidra-kör kell: 0x004e4ea0 - a +0x484 listában regisztrált DBLoader 0. slotját ténylegesen meghívó út, a param_2 objektum és param_2[2] felépítése, valamint bejárási sorrendje; a meglévő dekompilátum a regisztrációt mutatja, a hívót nem [blokkoló]`. `Ghidra-kör kell: 0x0055ece0 - a 0x00425f60 és 0x00456610 feltételek típusonkénti jelentése és az egyéb listaírók hatása; a meglévő dekompilátum a fogyasztó utasításait mutatja [blokkoló]`. Célzott Colab-mérés: két, különböző EXIF-dátumú kép és különböző videóformátumok bemeneti indexének és megjelenített albumpozíciójának naplózása, azonos, frissen létrehozott katalóguson; külön óraátállítási határeset.

**A #6532 készültsége.** Az eredeti videó korábban dokumentált (38.2.101 és 38.2.104). A teljes bináris spec, a teljes tételes eredeti/PicasaPy összevetés és a kiadási összehasonlító anyag nem teljes. A #6713 korábban megnyitott megvalósítási jegy a 38.2.102 eltéréseit fedi; állapota itt nem ellenőrizhető. A Recently Updated teljes fejlesztői jegytörzse a tagsági és sorrendi hiányok miatt nem írható meg bizonyítottan.

#### 38.2.120 Recently Updated: a feldolgozókapuk és a regisztráció határa (#6532, 2026-11-11)

**Hatókör és fok.** A `2026-11-11-6532-colab-decomp-11.txt`, a `2026-11-11-6532-colab-11-hivok.txt` és a `2026-11-11-6532-colab-11-484-irok.txt` meglévő Ghidra-kimenetét a megadott SHA-256 értékű helyi bináris célzott utasításaival vetettük össze. A kapuk alábbi ágai **feltételesen** igazoltak: a dekompilátum és a gépi kód ugyanazt az utat írja le, nem két független futás. A teljes tagság, a bemenet építése és a megjelenített sorrend **NINCS MEG**.

**A kapuk sorrendje.** A `0x0055eedc` az objektum `+0x29` bájtját vizsgálja; nulla esetén a `0x0055eef4` hívja a `0x00456610`-et. A `0x0055eef9` nemnullás visszatérésnél a `0x0055f849` ágra lép; különben a `0x0055ef15` hívja a `0x00425f60`-at, és a `0x0055ef1a` annak nemnullás visszatérését is ugyanoda irányítja. A hívások önmagukban nem azonosítanak felhasználói fájltípusokat vagy végső albumtagságot.

**A `0x00456610` két korai kimenetele.** Ha a `0x0045664a` által vizsgált bemeneti tároló üres, a `0x004566ce` a `0x004edf60` rekordlekérőt hívja. Ha a kitöltött descriptor jelzőbájtja nulla (`0x004566d3`), a függvény `9`-et ad vissza (`0x00456739`). Nem nulla jelzőnél a `0x0045674e` és `0x00456757` a descriptor típusát `0x19` és `0x1a` értékkel hasonlítja össze; egyezés esetén a `0x0045681a` nulla visszatérésére ugrik. Ez **nem** mondja ki, hogy e típusok bekerülnek az albumba: a másik kapu és a későbbi szűrők is számítanak. A többi típus teljes eredménye és a `0x00425f60` minden visszatérési útjának jelentése **NINCS MEG**.

**Regisztráció.** A `0x004e4ec7` és `0x004e4f59` a `+0x488` mezőből jobbra tolással indexet képez; a `0x004e4f4f` a `+0x484` mutatót olvassa, a `0x004e4f61` pedig ezen az indexen elhelyezi a regisztrálandó argumentumot. A kapott `484-irok` anyag írókat sorol, ezért nem bizonyítja a lista olvasóinak hiányát. A tényleges bejáró, a virtuális 0. slot hívásának argumentuma, kiváltó eseménye és a `param_2[2]` tömb építője és sorrendje **NINCS MEG**. A teljes `.text` pásztázás külső memóriakorlátja ebben a munkamenetben a felhasználói systemd busz elérhetetlensége miatt nem volt elindítható; ilyen pásztázás nem futott, negatív lelet ebből nem következik.

**Két út és cáfolat.** A: a friss Ghidra-kimenetek vezérlésfolyamának olvasása. B: a fenti hívó és célzott gépi utasítások ellenőrzése az azonos hashű helyi binárison. Egyeznek, de ugyanazt az utat mutatják, ezért a részletes áglelet feltételes. Független megfigyelés a Colab #545-#551 mérése: 24 friss kép bekerült, a megadott két pozíció nem fájlnév szerinti, és szerkesztés, mentés, újraindítás nem mozdította a mért képet. Ez nem méri a bemeneti tömböt, sem a 0x19/0x1a ágakat. Cáfoló feltevés: „a `0x19` és `0x1a` típusokat az első kapu nemnullás hibával zárja ki”. A fenti feltételes korai ágon a gépi kód és a dekompilátum egyaránt nulla visszatérést mutat; az általános típusonkénti tagságot ez sem dönti el.

| Állítás | Forrás |
|---|---|
| Első és második kapu nemnullás ága a `0x0055f849` címre jut | bináris (`0x0055eef4`-`0x0055ef1c`) |
| Üres bemeneti tároló mellett nulla descriptor-jelző esetén 9 a visszatérés | bináris (`0x0045664a`, `0x004566ce`-`0x00456744`) |
| A descriptor `0x19` és `0x1a` típusára a leírt ágon nulla a visszatérés | bináris (`0x00456747`-`0x0045675a`, `0x00456802`-`0x00456822`) |
| Regisztrációs tömbmutató és méretjelző | bináris (`0x004e4ec7`, `0x004e4f4f`-`0x004e4f77`) |
| A teszt 24 friss képét tartalmazza, két pozíció és változatlanság | mérés (Colab #545-#551, feladatátadás) |
| Bejáró, tömbépítő, teljes tagság és sorrend | NINCS MEG |

**Következő lépés.** `Ghidra-kör kell: 0x004e4ea0 - a meglévő kimenet csak a +0x484 lista regisztrációját mutatja; melyik azonosított objektummetódus járja be, és milyen eseménnyel, milyen argumentummal hívja a regisztrált DBLoader 0. slotját? [blokkoló]` `Ghidra-kör kell: 0x0055ece0 - a meglévő fogyasztó és kapudekompszöveg nem mutatja a param_2[2] tömb építőjét és sorrendjét; melyik út hozza létre és tölti fel? [blokkoló]` `Ghidra-kör kell: 0x00425f60 - a meglévő hosszú dekompilátum nem ad típusonkénti visszatérési és tagsági táblát; mely feltételek állítanak nemnullás eredményt a 0x0055ef15 hívásánál? [blokkoló]` Célzott Colab-mérés: azonos friss katalógusban a bemeneti rekordazonosítók és a megjelenített album teljes sorrendjének rögzítése, különböző kép- és videótípusokkal.

**A #6532 készültsége.** Az eredeti felvételek dokumentáltak (38.2.101 és 38.2.104). A teljes bináris spec és az eredeti/PicasaPy tételes összevetés nem teljes; a #6713 meglétét az átadás rögzíti, jelenlegi állapota itt nem ellenőrizhető. A kiadási összehasonlító videó vagy képsor nincs igazolva. A teljes tagság és sorrend hiányában új, végrehajtható fejlesztési jegytörzs nem következik ebből a körből.

#### 38.2.121 Recently Updated: a DBLoader meghívása és két tömbépítő út (#6532, 2026-11-11)

**Hatókör és bizonyítottság.** A regisztrációhoz tartozó bejáró és két bemenettöltő út azonosítható; a kapcsolódó utasítássorok **feltételesek**, mert a dekompiláció és az utasítások ugyanannak a végrehajtási útnak két olvasatai. A teljes eseményszemantika, a minden útból keletkező bemeneti sorrend, a típusonkénti teljes tagság és a megjelenített sorrend **NINCS MEG**. A helyi bináris SHA-256 értéke `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`, egyezik a Colab 12. kör forrásával.

**Bejáró és argumentum.** A `0x004e87c0` előbb az objektum `+4` virtuális metódusának eredményét vizsgálja (`0x004e87c0`-`0x004e87d3`); nemnullás eredménynél nem hívja a listát. Ezután a bemeneti objektum `+4` mezőjével hívott `0x004e39c0` eredményének `+0x18` mezője `1` vagy `0x19` kell legyen (`0x004e87df`-`0x004e87f5`). A `0x004e8806`-`0x004e882d` növekvő indexszel bejárja a `+0x484` mutatótömböt, a `+0x488 >> 1` elemszámig; a nemnullás elemek 0. virtuális slotját **ugyanazzal a bemeneti objektummutatóval** hívja (`0x004e8815`-`0x004e881e`). A lista és a regisztráció összekötése: `0x00403614`-`0x0040361c` és `0x004e4f4f`-`0x004e4f61`, lásd 38.2.115.

**A slot külön adatellenőrzése.** A `0x004035f5` a `0x00c7f5c0` táblát írja az objektumba; a PE-ből közvetlenül kiolvasott első táblaszó `0x0055ece0`, a második `0x0055ff50`, a harmadik `0x0055ff70`. A bináris index RTTI-rekordja ugyanezt a táblát `DBLoader::vftable` néven azonosítja. Ez a táblaadat és a konstruktor/regisztráció külön kapcsolódási út, amely egyezik a bejáró utasításaival; a tényleges esemény teljes jelentését nem méri.

**Egy bemenetépítő ág.** A `0x004e80d0` a vizsgált ágon a meghatározott csoportazonosító változásakor, ha az előző azonosító nem `0xffffffff`, átadja a korábbi bemeneti objektumot a `0x004e87c0`-nak (`0x004e84a8`-`0x004e84bb`). Utána a `0x004e3940` üríti az objektum `+8` tömbjét és `+0xc` elemszámmezőjét, majd az új azonosító kerül `+4`-re (`0x004e84c0`-`0x004e84cb`, `0x004e3942`-`0x004e3964`). A `0x004e84d8` a bemenethez adja a feldolgozott azonosítót a `0x004e39f0` útján. Utóbbi a meglevő elemszám által kijelölt helyre ír (`0x004e3a70`-`0x004e3a8f`): **ezen az ágon hozzáfűzési sorrend** van, ami nem bizonyítja az előállító forrásának általános sorrendjét.

**Másik bemenetépítő ág.** A `0x00503920` ugyanazzal a hozzáfűzővel építi egyik helyi bemenetét (`0x00503ef4`-`0x00503efc`, `0x005042a3`-`0x005042af`), és nem üres tömb esetén átadja a bejárónak (`0x00504642`-`0x00504659`). Egy későbbi ágon egy másik, a `0x004e5a80` eredményéből származó tömb elemeit index szerint fűzi hozzá (`0x00504812`-`0x00504821`), majd meghívja a bejárót (`0x00504aba`-`0x00504ac8`). Az itt és a `0x004e80d0` ágán hozzáfűzött bemenet egymástól külön építési út. A `0x0055ece0` a kapott `+8` tömböt növekvő indexszel fogyasztja (`0x0055ece0`, 12. dekompiláció); ebből nem következik, hogy a végső album ugyanilyen sorrendű.

**Cáfoló kör.** A „minden listaelem mindig a DBLoader feldolgozója, bármely bemenetre” állítást a nullmutató-ellenőrzés és a két belépési kapu cáfolja (`0x004e87d1`-`0x004e87f5`, `0x004e880c`-`0x004e8813`). A „minden feldolgozói slot ugyanaz” állítást a táblaszavak PE-ből kiolvasott különböző értékei cáfolják. Ezek a gépi adatok és utasítások feltételes szerkezeti cáfolatok; nem jelentenek külön futtatásos mérést. A Colab #545-#551 független megfigyelése 24 friss kép tagságát és a két megadott albumpozíciót méri, a belső argumentumot nem, ezért a teljes sorrendet nem igazolja.

| Állítás | Forrás |
|---|---|
| Bejáró, kapuk, 0. slot és argumentum | bináris (`0x004e87c0`-`0x004e882d`) |
| DBLoader táblájának első három szava | bináris (`0x00c7f5c0`, `0x00c7f5c4`, `0x00c7f5c8`) |
| Csoportváltás és hozzáfűzés egy építőúton | bináris (`0x004e84a8`-`0x004e84d8`, `0x004e3a70`-`0x004e3a8f`) |
| Másik építőút két hozzáfűzése és továbbítása | bináris (`0x00503efc`, `0x005042af`, `0x00504659`, `0x00504821`, `0x00504ac8`) |
| 24 friss kép és a két megadott pozíció | mérés (Colab #545-#551, feladatátadás) |
| Minden feldolgozási esemény, típusonkénti tagság és végső sorrend | NINCS MEG |

**Következő célok.** `Ghidra-kör kell: 0x004e80d0 - a meglévő 10. körös kimenet bemutatja a csoportváltást és a hozzáfűzést; milyen konkrét fájlrendszeri vagy katalógusesemények és milyen forrássorrend vezetnek erre az ágra? [blokkoló]` `Ghidra-kör kell: 0x004e5a80 - a 0x00503920 meglévő dekompilációja e függvény kimenetét fűzi a második bemenethez, de a kimenet eredete és sorrendje nem ismert; hogyan épül és rendeződik? [blokkoló]` `Ghidra-kör kell: 0x00425f60 - a 12. kör meglévő hívottlistája és dekompilációja nem ad teljes, a 0x0055ef15 hívás paramétereire szűkített típusonkénti visszatérési táblát; mely ágak és további feltételek vezetnek nullához vagy nemnullához? [blokkoló]` `Ghidra-kör kell: 0x00456610 - a 12. kör meglévő hívottlistája és dekompilációja nem ad teljes, a 0x0055eef4 hívás paramétereire szűkített típusonkénti visszatérési táblát; mely ágak és további feltételek vezetnek nullához vagy nemnullához? [blokkoló]` Mérési alternatíva: friss, különböző kép- és videótípusokat tartalmazó katalógusban a bemeneti azonosítók, az összes albumpozíció és a változást kiváltó esemény egyidejű naplózása.

**A #6532 készültsége.** Az eredeti videók dokumentáltak (38.2.101, 38.2.104); a teljes bináris spec és az azonos mintán elvégzett teljes összevetés nem kész. Az átadás szerint a #6713 megvalósítási jegy létezik, aktuális állapota itt nem ellenőrizhető. Kiadási összehasonlító videó vagy képsor nem igazolt. A teljes tagság és végső sorrend hiányában új fejlesztési jegytörzs nem állítható össze becslés nélkül.

##### 38.2.121/a A három helyi bináris cél eredménye (2026. november 12.)

**Hatókör és bizalmi fok.** A Picasa3.exe 3.9.141.259 helyi példányát vizsgáltam, SHA 256: `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. A következtetés **feltételes**: az utasítások és a meglévő dekompiláció együtt azonosítják a három út működését, de futásos megfigyelés nem történt, és néhány segédfüggvény szemantikája nyitva marad.

**A két független út.** A út: a `0x004ed5e0` utasításai virtuális `+8` hívást végeznek a `+0x54` objektumon, a `0x004e41f0` pedig `ytDirScanner` táblát ír ebbe az objektumba. B út: a PE `0x00c86be0` táblájának `+8` szava közvetlenül `0x004ebff0`, és az RTTI leltár ugyanezt a táblát `ytDirScanner::vftable` néven azonosítja. A két út a visszahívás címében egyezik. A listaírásnál az utasításszintű regiszterút `0x004ea360` felől a `0x004e5210` és `0x004e5070` függvényhez vezet; a külön teljes mezőpásztázás a `0x004e5070` függvényt azonosítja a `+0x3f0/+0x3f4` írójaként. Ezek a megfigyelések a belső lista írását megerősítik, a rejtett alias teljes kizárását nem.

**A visszahívás és a két külön tároló.** A `0x004ed5e0` a tulajdonos `+0x54` objektum virtuális `+8` helyét hívja az index átadásával (`0x004ed660`-`0x004ed668`). A `0x004e41f0` a `ytDirScanner` táblát írja az objektumba, a PE vtable `0x00c86be0` `+8` eleme pedig `0x004ebff0`. A `0x004e5a80` kimeneti indexvektorának címét a hívó adja át külön paraméterként; a `0x004ed5e0` sem ezt, sem a vektor címét nem továbbítja a visszahívásnak.

A visszahívás közvetett mellékhatása mégis látható. A `0x004ebff0` a saját objektummutatójával hívja a `0x004ea360` függvényt. A `0x004ea360` megfelelő eseményágában a `0x004e5210` a scanner objektummutatóját adja a `0x004e5070` függvénynek. Ez a függvény a scanner saját `+0x3f0/+0x3f4` pointerlistájához fűz `0x2c` bájtos rekordot, a darabszám utáni helyre. Ez a beágyazott scanner tárolója; nem a `0x004e5a80` hívója által átadott kimeneti indexvektor. A megvizsgált hívási út tehát belső rekordlistát módosít, a kimeneti vektor közvetlen vagy közvetett módosítására nem találtam adatutat. Rejtett globális alias teljes kizárása **NINCS MEG**.

**A `0x00425f60` kilépési EAX értékei.** A hívó `0x0055ef1a` címen teszteli az EAX értékét; nulla esetén továbbmegy, nem nulla esetén a `0x0055f849` címre ugrik. Az alábbi felsorolásban minden visszatérés előtti utolsó EAX író utasítás szerepel.

* `0x0042605f`: az utolsó író `0x00426046`, az érték 2.
* `0x0042617f`: az utolsó író `0x00426167`, mentett segédfüggvény-eredmény, a visszatéréshez nem nulla kell.
* `0x004261e0`: az utolsó író `0x004261c8`, mentett virtuális hívás eredménye, a visszatéréshez nem nulla kell.
* `0x004265ce`: az utolsó író `0x004265b5`, az érték `0xf4242`.
* `0x0042663c`: az utolsó író `0x00426624`, a `0x005b1570` hívás mentett EAX értéke.
* `0x004281e9`: az utolsó író `0x004281d0`, az érték 3, ha a méret vagy a számított kiterjedés nem pozitív.
* `0x00428400`: az utolsó író `0x004283ea`, EDI, csak nem nulla segédfüggvény-eredmény után.

A nulla visszatérés egyetlen lehetséges kilépése a `0x0042663c`: ehhez a `0x004265d1` által ellenőrzött helyi jelzőnek nem nullának kell lennie, és a mentett eredmény nem lehet `0xf4242`. A `0x005b1570` a kapott típusérték szerint választ segédfüggvényt, majd nulla segédfüggvény-eredményt is továbbvihet (`0x005b19bf`). A pontos típusok és azok feltételei, amelyeknél ezek a segédfüggvények nullát adnak, **NINCS MEG**. Biztosan nem nulla a másik hat kilépés EAX értéke.

**A `+0x538/+0x53c` sor forrása és sorrendje.** A `0x004e41f0` konstruktor nullázza a két mezőt (`0x004e44a2`, `0x004e44a8`); a `0x004e4960` felszabadítás után nullázza őket (`0x004e49f9`, `0x004e4a06`). Ugyanez a konstruktor nullázza a forráslisták `+0xe4/+0xe8` és `+0xec/+0xf0` mezőit (`0x004e4258`-`0x004e4272`), amelyeket a `0x004e4960` is ürít (`0x004e4e37`-`0x004e4e71`). A `0x004ea360` építi, majd feldolgozás után üríti a sort és e két forráslistát. A teljes mezőpásztázás egy további `+0xe4` írást talált a `0x004e2140` címen, de ez a `CChangeLoggerWindows` konstruktorának nullázása (`0x00c86d08` vtable), ezért nem a scanner forráslistájának írója. A forráslisták tényleges feltöltő útja **NINCS MEG**.

* A `+0x334/+0x338` bemenet elemeit növekvő indexben adja át a `0x00706c80` függvénynek.
* A `+0xe4/+0xe8` bemenet minden eleméből `3` értékű rekordot készít, és a sor végére fűzi (`0x004ea63a`, számláló növelése: `0x004ea681`).
* A `+0xec/+0xf0` bemenet minden eleméből `6` értékű rekordot készít, és a sor végére fűzi (`0x004ea9ed`, számláló növelése: `0x004eaa36`).
* A későbbi feldolgozó ciklus növekvő sorindexben olvas; a végén ürít (`0x004ebcbd`, `0x004ebccf`).

A `3` értékű rekord tehát a `+0xe4/+0xe8` bemeneti lista egyik eleme. A feldolgozás a `0x004e7ec0` úton folytatódik. A kód nem nevezi meg e rekord emberi fájlrendszeri jelentését, ez **NINCS MEG**. A `0x004ea360` és a `0x00706c80` vizsgált útjában rendező hívás nem látható: a bemeneti elemek indexben haladnak, a kimeneti sorhoz hozzáfűződnek, és a sor feldolgozása is növekvő indexben történik. A bemeneti listák előzetes sorrendje és az esetleges másutt végzett rendezés **NINCS MEG**.

**Cáfoló kísérlet.** A kimeneti indexvektorra írás hiányát azzal próbáltam cáfolni, hogy végigkövettem a `0x004ebff0` statikus hívási útján a `+0x3f0/+0x3f4` mező íróit. A keresés elérte a `0x004e5070` függvényt, amely valóban hozzáfűz egy rekordot, de a regiszterút azonosította, hogy az írás a scanner objektum saját tárolójába megy. A kimeneti vektor címe nincs jelen a visszahívás argumentumai között. Ez cáfolja a „nincs mellékhatás” állítást, de nem bizonyítja rejtett alias teljes hiányát. A rendezésre vonatkozó állítást is cáfoló irányból ellenőriztem: a három bemeneti ciklus és a sor feldolgozása indexet növel, a vizsgált útban összehasonlító vagy átrendező lépés nem került elő.

**Bizonyíték.**

* A virtuális `+8` célja `0x004ebff0`: bináris (`0x004e41f0`, `0x00c86be0`, `0x004ed660`-`0x004ed668`).
* A scanner belső listájához rekordot fűz: bináris (`0x004eb554`, `0x004e542d`-`0x004e542f`, `0x004e5070`).
* A `0x00425f60` hét visszatérési címének utolsó EAX írója: bináris (`0x00426046`, `0x00426167`, `0x004261c8`, `0x004265b5`, `0x00426624`, `0x004281d0`, `0x004283ea`).
* A `+0x538/+0x53c` mezők inicializálása, bővítése és ürítése: bináris (`0x004e41f0`, `0x004e4960`, `0x004ea360`).
* A három bemenet bejárási iránya és rekordfűzése: bináris (`0x004ea360`, `0x00706c80`).
* A kimeneti indexvektor rejtett alias útjának teljes kizárása: NINCS MEG.
* A `3` rekord emberi jelentése és a bemeneti listák előzetes sorrendje: NINCS MEG.

##### 38.2.121/b A hétnapos kapu és a DBLoader nulladik slotja (2026. november 12.)

**Hatókör és bizalmi fok.** A helyi Picasa3.exe 3.9.141.259 SHA 256 értéke `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. A `]updated` mezőpárja, a hétnapos küszöb és a DBLoader nulladik slotjának hívása **megerősített**, mert az utasításút és a külön rekordíró vagy vtable adatút egyezik. A lista összes kiváltó eseményének emberi jelentése **NINCS MEG**.

**A `]updated` kapu az első FILETIME párt vizsgálja.** A `0x0055ece0` a `0x004edf60` lekérővel másolja ki a rekordot. A lekérő mindkét időpárt változatlanul viszi át: az elsőt a `+4/+8`, a másodikat a `+0xc/+0x10` mezőről (`0x004ee08a-0x004ee09f`). A kapu a kimeneti leíró `+4` címét adja a dátumkonverternek (`0x0055f093-0x0055f099`), ezért a `+4/+8` pár a bemenete, a második pár nem. A `0x0055f0a1` a 7 értéket adja át a `0x0098b770` segédnek; ez az aktuális időből `7 × 0x15180` másodpercet számol (`0x0098b77e-0x0098b78e`), ahol `0x15180` pontosan 86400 másodperc (`0x0098b783`). A határ és a rekordból átalakított dátum összevetése a `0x0055f0b3` utasításnál történik.

**A mező jelentésének külön útja.** A `0x0040f980` rekordépítő a kapott FILETIME értékét mindkét párba bemásolja (`0x0040f9b6-0x0040f9db`). Ettől külön a metaadatíró út a `0x37` kulcshoz tartozó konvertált értéket a rekord `+4` címére írja (`0x00425f60`, `0x00427844`, `0x00427898`, `0x004eeb6d-0x004eebad`). A `0x37` kulcs `DateTimeOriginal` jelentését a metaadatkulcsok spec táblája és a bináris metaadatnév egymástól függetlenül támasztja alá (`0x00c9f064`). Így a kapu első párja olyan mező, amelyet az EXIF `DateTimeOriginal` felülírhat. A kapu nem a `+0xc/+0x10` mezőpárt olvassa.

**A DBLoader regisztrációja és a listabejáró.** A `0x004e4ea0` a megadott objektumot a `+0x484` pointerlistába fűzi, és a `+0x488` elemszámot növeli (`0x004e4f5f-0x004e4f61`). A listát a `0x004e87c0` járja be. A `+0x488` kódolt darabszámát használja, a nemnullás bejegyzések vtable első slotját hívja, a listában levő objektumot `ECX` regiszterbe, a bemenetként kapott eseményobjektumot pedig argumentumként adja át (`0x004e8806-0x004e882d`). A DBLoader konstruktor a `0x00c7f5c0` vtable címét írja az objektumba (`0x004035f5`); a PE táblájának első szava `0x0055ece0`, tehát ez a DBLoader nulladik slotja. A `0x004183c0` regisztrációs hívó a létrehozott DBLoader objektumot a `0x004e4ea0` regisztrációs függvényhez adja (`0x00403614-0x0040361c`, `0x004188cf`).

**Igazolt kiváltó út.** A `0x004e80d0` a `0x004e84a8-0x004e84bb` ágban meghívja a listabejárót, ha az új csoportkulcs eltér az előzőtől, és az előző kulcs nem `0xffffffff`. Argumentumként az előző eseményobjektum `EDI` mutatóját adja át. Ez a csoportkulcs váltásakor végrehajtott feldolgozási út. A `0x004e87c0` további közvetlen hívói miatt ez nem az egyetlen listafeldolgozási út: hét közvetlen hívó van az indexben, és a további helyek utasításai is a `0x004e87c0` hívását mutatják. A többi esemény teljes emberi jelentése **NINCS MEG**. A bejáró a bemeneti objektum `+4` virtuális lekérdezésének nemnullás eredményénél leáll, majd csak akkor hívja a listát, ha a `0x004e39c0` lekérdezés eredményének `+0x18` mezője 1 vagy `0x19` (`0x004e87c0-0x004e87f5`).

**A két független út.** A út: a `0x0055ece0` utasításai a `0x004edf60` által kiadott rekord `+4/+8` párját alakítják dátummá, majd a hét napos küszöbhöz hasonlítják. B út: a rekord külön metaadatírója a `0x37` `DateTimeOriginal` értéket a `+4` mezőbe írja; a rekordépítő mindkét pár külön kezdeti helyét igazolja. A mezőazonosítás egyezik. A DBLoader esetén A út: a `0x004e87c0` betölti a listaobjektum vtable táblájának első szavát, és azt hívja. B út: a DBLoader konstruktorában beállított cím és a nyers PE vtable első szava ugyanazt a `0x0055ece0` célt adja; a regisztráció hívási útja ezt a DBLoader objektumot teszi a listába. A két út a hívott nulladik slot célfüggvényében egyezik. Az argumentumot a `0x004e80d0` hívó és a `0x004e87c0` bejáró utasításainak összekapcsolása határozza meg.

**Cáfoló kísérlet.** Azt a lehetőséget vizsgáltam, hogy a `]updated` a második FILETIME párt olvassa. A getter valóban kiadja mindkét párt, de a kapu kizárólag a kimenet `+4` címét adja a dátumkonverternek; a külön metaadatíró út a `0x37` értéket ugyanerre a `+4` mezőre írja. A második pár hipotézise ezért cáfolódik két külön adatúton. Azt is vizsgáltam, hogy a bejáró a DBLoader másik metódusát hívja. Az utasítás `[vtable]` első szavát tölti be, a DBLoader nyers PE táblájának első szava pedig `0x0055ece0`, a második `0x0055ff50`; a második slot feltevése cáfolódik. Végül az egyetlen esemény hipotézisét a hét közvetlen hívó cáfolja. A megerősített gépi út azt rögzíti, hogy a csoportkulcs váltása egy igazolt kiváltó ok; a többi esemény emberi szemantikáját nem állítja.

**Bizonyíték.**

* A `]updated` kapu a `+4/+8` párt alakítja dátummá. Forrás: bináris (`0x004edf60`, `0x0055f093-0x0055f0b3`).
* A hétnapos időhatár pontos szorzója `7 × 0x15180`, ahol `0x15180` 86400. Forrás: bináris (`0x0055f0a1`, `0x0098b770`, `0x0098b783`).
* A `+4` mezőt `DateTimeOriginal` felülírhatja. Forrás: bináris (`0x00425f60`, `0x004eeb10`, `0x00c9f064`).
* A `+0x484` listát a `0x004e87c0` járja be, és a vtable első slotját hívja az eseményobjektummal. Forrás: bináris (`0x004e4ea0`, `0x004e87c0`, `0x004e8815-0x004e882d`).
* A DBLoader nulladik slotja `0x0055ece0`. Forrás: bináris (`0x004035f5`, `0x00c7f5c0`, `0x004e881b`).
* Csoportkulcs váltásakor az előző eseményobjektum a callback argumentuma. Forrás: bináris (`0x004e80d0`, `0x004e84a8-0x004e84bb`).
* A többi kiváltó esemény emberi jelentése: NINCS MEG.

**A 38.2.121/a pontosítása.** A `0x004e87c0` bejáróra és a DBLoader slotjára vonatkozó korábbi nyitott kérdés most lezárható a fenti gépi feltételekkel. A bejáró összes eseményének termékszintű megnevezése továbbra is nyitott. A hétnapos kapu a `+4/+8` első párt olvassa; ez nem bizonyítja, hogy minden rekordban ez a pár EXIF dátumot tartalmaz.

#### 38.2.122 Recently Updated: az új rekordok indexeinek előállítása (#6532, 2026-11-11)

**Hatókör.** A 38.2.121 négy kérdéséhez a `2026-11-11-6532-colab-12-olvasok-hivok.txt` és a `2026-11-11-6532-colab-decomp-12.txt` meglévő dekompilációit, valamint a 3.9.141.259 bináris helyi utasításait vizsgáltam. A SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. Új Ghidra-futtatás és új felvétel nem történt.

A feladat kiegészítésében külön kiemelt qshow `[this+0x2e4]` képszolgáltató virtuális `+8` célja már lezárt a 38.2.97-ben: `0x00424b10`. Ez másik hívási út, mint az alább vizsgált `ytDirScanner` `[this+0x54]` callback.

**A 0x004e5a80 eredménytömbje.** A függvény a bemeneti rekordszámot a második argumentum `+4` mezőjéből `>> 1` művelettel, a korábbi rekordszámot a kezelt objektum `+0x3f4` mezőjéből `>> 1` művelettel olvassa (`0x004e5acd`-`0x004e5ada`). A `0x004e5b22`-`0x004e5b45` ciklus a bemeneti rekordokon `0x2c` bájtonként előrehaladva másol a `+0x3f0` tároló bővített részébe. A `0x004e5d38`-`0x004e5d45` ciklus a kimeneti tömb `i` elemébe a **korábbi rekordszám + i** értéket írja, növekvő `i` mellett. Ez a ciklus nem összehasonlító rendezést, hanem összefüggő növekvő indexsorozatot állít elő. Az ezt követő `0x004ed5e0` hívásnak a kód a kezdő indexet, az objektumot és a darabszámot adja át (`0x004e5d47`-`0x004e5d4f`); a kimeneti tömb mutatóját nem. A hívás virtuális metódust is használ (`0x004ed660`-`0x004ed668`), ezért a tömb későbbi érintetlensége pusztán ebből nem bizonyított.

**Fogyasztás és korlát.** A `0x00503920` meglévő dekompilációja a `0x004e5a80` sikeres visszatérése után a `local_1214[i]` elemeket sorrendben adja át a `0x004e39f0` hozzáfűzőnek; a tömbolvasás és a hívás az utasításokban is látszik (`0x00504812`-`0x00504821`). A korábbi `0x0055ece0` dekompiláció a kapott indexek növekvő bemeneti pozíciók szerinti bejárását mutatja. Az indexsor eredete és az azt feldolgozó út így összeköthető, de az eredeti rekordok létrehozási sorrendje, a köztes hívások minden mellékhatása és a végső megjelenítési sorrend **NINCS MEG**. A `0x004edf60` külön leolvasója az indexet a `+0x3f0` tárolóba indexeli, majd a kiválasztott rekord mezőit másolja; ez alátámasztja az indexek rekordazonosító szerepét, de nem igazol albumsorrendet (`2026-11-11-6532-colab-12-olvasok-hivok.txt`, `0x004edf60`).

**Esemény és tagság.** A 12. körös `0x004ea360` dekompilációja a `+0x538` mutatóval és `+0x53c` számlálóval jelölt, `0x18` bájtos rekordok növekvő indexű bejárását mutatja; a `0x004e80d0` egyik hívása a rekord első szavának `3` értékű ágában található. A `3` konkrét fájlrendszeri jelentése és a rekordok betöltés előtti sorrendje **NINCS MEG**. A 14. kör `0x00456610` dekompilációja szerint a `0x004edf60` utáni rekordjelző érvénytelen esetén `9`-et ad vissza; a többi visszatérési út `0`-t ad (`0x00456739`, `0x0045681a`, `0x0045688f`, `0x0045a9ba`). A `0x0055ece0` a `0x00456610` hívás után vizsgálja az EAX-ot (`0x0055eef4`-`0x0055eef9`): a nem nulla érték elutasító ágra jut, a nulla érték engedi tovább a `0x00425f60` kapuhoz (`0x0055ef15`). Ez a számszerű kapu viselkedését írja le, de a típusértékek emberi jelentését és a teljes tagságot nem.

**A 13-14. Ghidra-kör callbackje és az indexvektor.** A vizsgált kimenetek: `2026-11-11-6532-colab-decomp-13.txt`, `2026-11-11-6532-colab-decomp-13-celok.txt`, `2026-11-11-6532-colab-decomp-14.txt` és `2026-11-11-6532-colab-decomp-14-celok.txt`. A `0x004e5a80` a kimeneti indexvektorba növekvő `i` mellett `korábbi_darabszám + i` értékeket ír (`0x004e5d38`-`0x004e5d45`), majd a `0x004ed5e0` hívásnak a kezdő indexet EAX-ban, a darabszámot és a tulajdonos objektumot adja át (`0x004e5d47`-`0x004e5d4f`); az indexvektor címét nem adja át. A `0x004ed5e0` a `[this+0x54]` objektum virtuális `+8` slotját hívja indexenként (`0x004ed660`-`0x004ed668`). A `0x004e41f0` konstruktor a `ytDirScanner::vftable`-t írja a beágyazott `+0x54` objektumba; a helyi bináris nyers PE-vtable adatában a `0x00c86be0` tábla `+8` slotja `0x004ebff0`. Ez a konkrét hívási cél a konstruktor/vtable adatút és a `0x004ed5e0` hívóhelyének külön ellenőrzésével egyezik.

**Cáfoló kísérlet és határ.** Azt a feltevést próbáltam cáfolni, hogy a callback közvetlenül az indexvektorba ír vagy azt rendezi. A hívó nem adja át a vektor címét, a callback indexet kap; külön fogyasztóként a `0x00503920` a `0x004e5a80` visszatérése után olvassa a vektort és adja az indexeket a `0x004e39f0` hozzáfűzőnek (`0x00504812`-`0x00504821`). Ez a közvetlen, átadott mutatón keresztüli módosítást cáfolja, de a más mutatón át vagy más közvetett úton okozott mellékhatást nem. A meglévő 13/14-es Ghidra-kimenetek és a `referencia/ghidra/*.txt` leltára nem tartalmazza a `0x004ebff0` teljes dekompilációját; a helyi diszasszemblálás önmagában nem zárja ki a közvetett írást.

**A dátummezők határa.** A 14. kör `0x004e62d0` dekompilációja a `local_e68[0x87]` és `[0x88]` értéket egy meglévő rekord `+0x0c` és `+0x10` mezőjébe másolja. A kimenetből és az eddigi célzott utasításolvasásból nem állapítottam meg, ki tölti fel a `local_e68` e két mezőjét, illetve milyen naptári eseményt jelentenek. A fájlmódosítási idő, létrehozási idő vagy adatbázisba vételi idő **NINCS MEG**.

**Bizonyítottság és cáfolat.** A tömbíró ciklus és az azt fogyasztó utasítások leolvasása **feltételes**, mert a dekompiláció és diszasszembly ugyanannak a kódútnak két olvasata; a `0x004edf60` független rekordolvasó csak az index szerepét támasztja alá. Cáfolatként megvizsgáltam, hogy a tömbíró ciklus rekordértékek összehasonlításával rendezi-e a kimenetet: a ciklus csak az induló számláló és az egyesével növelt index összegét írja (`0x004e5d38`-`0x004e5d45`), így ez a feltevés erre a ciklusra nem áll. Ez nem zár ki másutt végzett rendezést. A Colab #545-#551 mérése szerint 24 friss kép szerepelt az albumban, a gray_ramp a 21., a színtábla a 24. volt, és szerkesztés, mentés, majd újraindítás nem változtatott ezen; ez független mérés, de a belső indexsorozatot nem figyelte meg.

| Állítás | Forrás |
|---|---|
| Korábbi darabszám + i szerinti kimenet | bináris (`0x004e5acd`-`0x004e5ada`, `0x004e5d38`-`0x004e5d45`) |
| A kimenet elemeinek továbbadása | bináris (`0x00504812`-`0x00504821`) |
| A külön rekordolvasó indexeli a `+0x3f0` tárolót | bináris (`0x004edf60`; 12. körös hívottak listája) |
| Mintafuttatás tagsága és két pozíciója | mérés (Colab #545-#551, feladatátadás) |
| A teljes típusonkénti tagság, a 3-as esemény jelentése és a végső sorrend | NINCS MEG |
| A `0x00456610` numerikus kapuja (9 az érvénytelen descriptorra, egyébként 0) | bináris (`0x00456739`, `0x0045681a`, `0x0045688f`, `0x0045a9ba`; feltételes, Ghidra 14 + utasításolvasás) |
| A `0x004ed5e0` virtuális `+8` célja | bináris (`0x004e41f0`, vtable `0x00c86be0`, `0x004ed660`-`0x004ed668`; megerősített) |
| A callback által okozható közvetett indexvektor-módosítás | NINCS MEG |
| A `0x004e62d0` által másolt két dátummező emberi jelentése | NINCS MEG |

**Következő célok.** `Ghidra-kör kell: 0x00425f60 - a 14. kör teljes dekompilációja void visszatérést mutat, miközben a 0x0055ef15 hívó az EAX-ot teszteli; a meglévő kimenet nem adja meg a kilépési pontok EAX-értékét. Milyen típusokra és feltételekre igaz a hívó által vizsgált nulla/nem nulla eredmény? [blokkoló]` `Ghidra-kör kell: 0x004ea360 - a 12. kör dekompilációja a 3-as eseményágat mutatja, a 13/14. kör pedig csak a 0x004e80d0 hívóutat; honnan töltődik a +0x538/+0x53c sor, mi a 3-as esemény és rendezik-e a sort? [blokkoló]` `Ghidra-kör kell: 0x004ebff0 - a meglévő 13/14. kör nem tartalmazza a 0x004ed5e0 által meghívott konkrét ytDirScanner-metódust; hozzáfér-e közvetetten a kimeneti indexvektorhoz, és milyen mellékhatásai vannak? [blokkoló]` A `0x004e62d0` két másolt dátummezőjének forrása és jelentése **NINCS MEG**; a teljes albumsorrendet pedig a végigkövetett út és az azonos mintán végzett mérés együtt tudja eldönteni.

**A #6532 készültsége.** ✅ Az eredeti felvételek a 38.2.101 és 38.2.104 szakaszban dokumentáltak. ⛔ A teljes, bináris címekkel igazolt spec és az azonos mintás összevetés hiányzik. ✅ Az átadás szerint a #6713 megvalósítási jegy létezik, állapota helyben nem ellenőrizhető; ⛔ a kiadási összehasonlító videó vagy képsor nem igazolt. A tagság és sorrend hiányában ebből a körből nem adható becslésmentes Recently Updated fejlesztési jegytörzs.

#### 38.2.123 Recently Updated: a rekord FILETIME eredete, a kapuk és a sorrend mérése (#6851, 2026-11-12)

**Hatókör és források.** A 13. és 14. Ghidra-dekompilációs kör kimeneteit (a privát tár `referencia/ghidra/` alatt: `2026-11-11-6532-colab-decomp-13.txt`, `2026-11-11-6532-colab-decomp-13-celok.txt`, `2026-11-11-6532-colab-decomp-14.txt`, `2026-11-11-6532-colab-decomp-14-celok.txt`) és a Colab #609, #611 futtatásos méréseit vizsgáltuk a 3.9.141.259 bináris (SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`) Recently Updated tagsági és rendezési szabályainak lezárásához.

**A 0x00456610 kapu és visszatérési értékei.** A `0x00456610` dekompilációja szerint a függvény kizárólag érvénytelen descriptor esetén tér vissza nem nulla (konkrétan 9) értékkel (`0x00456739`), ha a `0x004edf60` hívás után a rekord jelzőbájtja nulla (`0x004566d3`). Minden más esetben nulla (EAX == 0) a visszatérési érték: a `0x19` és `0x1a` típusoknál a korai `0x0045681a` ágon, üres szűrőlistánál a `0x0045684d` / `0x0045685a` ágon, valamint a teljes feldolgozási ciklus végén a `0x0045a90a` címen is (`return 0;`). A `0x0055ece0` feldolgozóban a `0x0055eef4` hívás az első kapu (`param_3 = 2`): a nem nulla visszatérés (9) elutasítja a rekordot (`0x0055eef9` -> `0x0055f849`), míg a nulla visszatérés átengedi a rekordot a második kapura (`0x00425f60` a `0x0055ef15`-nél), majd a `0x0055ef45` híváshoz (`param_3 = 1`), amely a `local_a60` kimeneti mutatóval a `0x004b9ed0` hívást készíti elő. A 0-s visszatérés tehát szükséges előfeltétele annak, hogy a rekord eljusson a Recently Updated (`]updated`) dátum- és korlát-ellenőrzéséhez.

**A 0x00425f60 kapu típus- és feltételkezelése.** A 14. kör dekompilációjában a `0x00425f60` szignatúrája `void`, és minden kilépési pontján sima `return;` szerepel C szinten (`0x00426046`, `0x00428194`, `0x004283c6`, `0x004265ef`, `0x00428fe5`). A Ghidra C-kódjából az EAX regiszter kilépési értéke közvetlenül nem olvasható ki, így a pontos, típusonkénti EAX=0 visszatérési szabály ebből a kimenetből **NINCS MEG**. A vezérlési ágakból azonban azonosítható, hogy a `local_1760 == 4` típus azonnali korai kilépést okoz (`0x00426d69` -> `0x00426046`), valamint külön feltételes ágat képeznek a `0x08`, `0x09`, `0x0a`, `0x0b`, `0x0c`, `0x17`, `0x1d` típusok (`0x00426c10` / `0x00427a70`), illetve a `0x15`, `0x18`, `0x1a` típusok (`3536-3541. sor`).

**A rekord FILETIME mezőjének (+4/+8) eredete - korrekció.** A `0x004e62d0` `0x004e753f`-`0x004e7555` utasításai a scanner `+0x21c/+0x220` mezőiből adják át a kezdeti időt a `0x0040f980` rekordépítőnek; a konstruktor `0x0040f9b6`-`0x0040f9db` ezt mindkét időpárba bemásolja. Ez a rekordépítés kezdeti értékét igazolja, nem a mezők minden későbbi állapotát. A `0x00427844` `0x37` kulcsú metaadatút és a `0x004eeb10` első mezőre író hívás bizonyítéka, valamint a két független út és a cáfoló próba a 38.2.121/a szakaszban szerepel. A 38.2.123 korábbi „egyértelműen fájl-módosítási idő” következtetése ezért túl általános: a sikeres `0x37` olvasás az első időpárt EXIF `DateTimeOriginal` értékre állíthatja; a `pmp-database.md` 10.3/15.1 szerinti dátumbeállító utak később szintén módosíthatják. A `0x004edf60` descriptor-másolása és a `0x0055ece0` hétnapos összehasonlítása a kiválasztott rekord első időpárját használja, amely nem minden esetben fájl-módosítási idő. A tényleges albumtagság, a `0x3e9` átirányítások és a futásidejű értékek teljes lefedése **nyitott**.


**A 0x004ed5e0 és az értesítési sorrend.** A `0x004ed5e0` (`7562-7603. sor`) az eredménytömb mutatóját nem kapja meg argumentumként (`param_1` objektum, `param_2` darabszám, `in_EAX` kezdő index), a tömb memóriájához nem fér hozzá, és az eredménytömböt **nem módosítja**. A feldolgozókat (a `*(int *)(param_1 + 0x54) + 8` virtuális callbacket és a `FUN_009bbb70` hívást) **növekvő index szerinti sorrendben** értesíti, az `in_EAX` kezdőértéktől az `in_EAX + param_2 - 1` végértékig egyenként lépegetve (`0x004ed5e0`, 7592-7598. sor).

**Mérés (Colab #609, #611).** Friss katalógusban mind a 24 minta-kép tagja a Recently Updated albumnak. A katalógus rekordsorrendje (thumbindex) a fájlnevek szerinti beolvasási sorrend, és a megjelenített Recently Updated album a katalógus rekordsorrendjének **fordítottja**: a legutóbb felvett rekord áll a lista elején (a k-adik cella a (25 - k)-adik rekordnak felel meg, átlagszín-párosítással ellenőrizve). Ez igazolja a `0x0055ece0` kódjában talált `0x006c9e80` hívást, amely minden elfogadott elemet a lista 0. pozíciójára (elejére) szúr be.

| Állítás | Forrás |
|---|---|
| A `0x00456610` csak érvénytelen descriptorra ad 9-et, egyébként 0-t | bináris (`0x004566d3`-`0x00456739`, `0x00456802`-`0x0045681a`, `0x0045a90a`) |
| A `0x0055ece0` első kapuja (`0x0055eef4`) a 9-es értékre kizárja a rekordot | bináris (`0x0055eef4`-`0x0055eef9`, `0x0055f849`) |
| A `0x00425f60` void dekompilációja miatt az EAX=0 visszatérési tábla | NINCS MEG |
| A `0x00425f60` a 4-es típusra azonnal kilép a `0x00426046`-ra | bináris (`0x00426d69`, `0x00426046`) |
| Rekordépítéskor mindkét FILETIME-pár `ftLastWriteTime`; a sikeres `0x37` metaadat-olvasás az első párt felülírhatja. | bináris (`0x004e753f`-`0x004e756a`, `0x0040f980`); a felülíró út és független metaadatkulcs-tábla: 38.2.121/a (`0x00427844`, `0x00427898`, `0x004eeb10`, `0x00c788d8`) |
| A `0x004ed5e0` nem módosítja a tömböt, növekvő indexekkel értesít | bináris (`0x004ed5e0`-`0x004ed603`) |
| Friss katalógusban 24 kép tag; a sorrend a rekordsorrend fordítottja | mérés (Colab #609, #611) |
| A `0x0055ece0` a 0. pozícióra szúr be elemeket (`0x006c9e80`) | bináris (`0x0055f0db`-`0x0055f191`, `0x006c9e80`) |

**A #6532 és #6851 készültsége.** ✅ Rekordépítéskor mindkét FILETIME-pár kezdeti értéke `ftLastWriteTime`; a sikeres `0x37` metaadat-olvasás az első párt EXIF `DateTimeOriginal` értékre írhatja át (38.2.121/a két úton ellenőrizve). ⛔ A `]updated` hét napos kapujában az egyes katalógusrekordoknál ténylegesen használt dátum és a teljes tagsági szabály nyitott; a mező nem nevezhető általánosan fájl-módosítási időnek. ✅ A sorrend szabálya bizonyított és méréssel igazolt: az album a bemeneti rekordsorrend fordítottja (legutóbb hozzáadott rekord elöl), legfeljebb 250 elemig (`RecentLimit`), a hétnapos küszöb a descriptor első időpárját használja. ✅ A `0x00456610` kapu szerepe és 0-s előfeltétele tisztázott. ⛔ A `0x00425f60` pontos típusonkénti visszatérési értékei a dekompilátum void szignatúrája miatt közvetlenül nem igazoltak (utasításszintű olvasás vagy futási mérés szükséges a típusonkénti lefedettséghez).

##### 38.2.121/c A `0x004e87c0` hat további hívója és a PicasaPy hétnapos dátumkulcsa (#6532, 2026. november 13.)

**Hatókör és bizonyítottság.** A Picasa 3.9.141.259 helyi binárisát vizsgáltam, SHA-256: `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. A `0x004e87c0` hat, korábban itt nem részletezett közvetlen hívóját a binary-index `xrefs` táblája és a helyi `annot_disasm.py` külön-külön is megadja. A releváns meglévő dekompilációk a privát kutatási repó `2026-11-11-6532-colab-decomp-13.txt`, `2026-11-11-6532-colab-decomp-14.txt` és `2026-11-11-6532-colab-12-olvasok-hivok.txt` fájljaiban vannak. Új Ghidra-kör és futásidejű tagságmérés nem történt.

Az alábbi eseményobjektumok mind stack-local rekordok. A hívóhely bizonyítja a rekord címének átadását, de a rekord minden mezőjének emberi jelentését nem. A műveletcsaládot a második, külön út köti termékszintű kódhoz. Az összes alábbi besorolás **feltételes**: egyik út sem figyelte meg futás közben, hogy a rekord hatására egy kép ténylegesen bekerült-e a `]updated` albumba.

| Közvetlen hívó és eseményrekord | A út: utasítások és hívási sorrend | B út: független kapcsolat és termékművelet | Cáfoló kísérlet és eredmény |
|---|---|---|---|
| `0x004e62d0`, `local_e14`, átadás: `0x004e7941` | A `0x004e7896` a `0x00501570` segédet hívja a helyi rekorddal, majd a `0x004e793c`-`0x004e7941` utasítások átadják ugyanezt a rekordcímet a dispatchernek. | Az `0x004e62d0` közvetlen hívója `0x004e7d10`; ez scanner-útból is elérhető (`0x004e9400`, `0x004e9b00`, `0x004ea360`). A `0x00501570` utasításai a `.picasaoriginals`, `Originals`, `.picasa.ini` és `Picasa.ini` neveket használják. A bizonyított műveletcsalád sidecar/Originals metaadat-könyvelés a scanner útján. | A kézi szerkesztés-mentés feltételezését ellenőriztem a közvetlen hívási láncokkal: a wrapper scanner-útból is hívódik, ezért a kód nem azonosít egyetlen felhasználói gombot vagy mentési műveletet. Konkrét user-trigger: **NINCS MEG**. |
| `0x004e9400`, `local_64`, átadások: `0x004e969f`, `0x004e975b` | Mindkét callsite ugyanazt a 12 bájtos helyi rekordot adja át. A függvény eseményrekordokat dolgoz fel, és a hívások eltérő vezérlési pontokon vannak. | A `ytDirScanner::vftable` (`0x00c86be0`) `+8` slotja `0x004ebff0`; a scanner visszahívási útján a `0x004e9400` és `0x004ea360` is szerepel. A függvény Win32 `WaitForMultipleObjects`-t használ. Ez könyvtárfigyelő/scanner-események feldolgozása. | A „csak a teljes scan végén küldi” feltevést a két különböző callsite cáfolja: a `0x004e969f` a ciklusbeli feldolgozási útban van, a `0x004e975b` pedig egy másik lezárási ágon. Az eseménykódok fájlszintű jelentése: **NINCS MEG**. |
| `0x004ea360`, `piStack_2238`, átadás: `0x004ebce1` | A `+0x538/+0x53c` eseménysor bejárása és ürítése után, ha a helyi feltétel teljesül, a `0x004ebcd7`-`0x004ebce1` a veremrekordot küldi a dispatchernek. | A hívási lista `0x004e9400`, `0x004e9b00` és `0x004ebff0` felől ide vezet; a `0x004ebff0` a scanner vtable `+8` slotja. Ez a scanner callbackek eseménykötegének feldolgozása. | A „minden kötegbejegyzés backuphash-változás” feltevést a belső típuság cáfolja: az `0x004ea360` vizsgált útján a `9` kódú rekord hívja a `0x00507f60` feldolgozót. Más rekordtípusok emberi jelentése és tagsága: **NINCS MEG**. |
| `0x004f93f0`, `local_60`, átadás: `0x004f942b` | Előbb a `0x004e80d0` tölti a helyi rekordot az argumentumokkal és a `1,1,0` jelzőkkel; csak akkor következik a dispatch, ha a helyi maszk és az azonosító feltétele teljesül. | A `0x0042e110` a `CThumbDB::vftable` tagja, és `render:%d` xrefet tartalmaz. Külön hívási út vezet a `0x004f92c0`-n át a `0x0053de70` és `0x0057d080` függvényekhez; ezekhez `CThumbUI::screensaved` és `CThumbUI::clickview` xref tartozik. Ez render/screenshot/view jellegű műveletcsaládot támaszt alá. | Az általános szerkesztés-mentés besorolást a `clickview` út cáfolja: a hívási kör nem kizárólag szerkesztési mentés. A pontos esemény és az, hogy ez hozzáad-e képet a `]updated` listához: **NINCS MEG**. |
| `0x00503920`, `local_1120` és `auStack_1180`, átadások: `0x00504659`, `0x00504ac8` | Két külön bemeneti ág külön stack-local rekordot épít, majd mindkettőt továbbítja. Az egyik ágon a `0x00501570`, a másikon a `0x004e5a80` indexkimenete szerepel. | Egyetlen közvetlen hívója a `0x00505030`; ehhez a függvényhez tartozó string/xref útban `iPhotoSupportEnabled`, `AlbumData.xml`, `Previews` és `Thumbnails` található. Ez iPhoto-katalógus beolvasási/import út. | A „csak egyféle rekord, egyetlen bemeneti lista” feltevést a két külön rekord és a két külön építőág cáfolja. Hogy az iPhoto import mely képei kerülnek a `]updated` albumba: **NINCS MEG**. |
| `0x00507f60`, `auStack_64`, átadás: `0x00508843` | A függvény a `backuphash` mezőt felismerő és állapotot frissítő ágban építi az eseményrekordot, majd feltételesen továbbítja. | A `backuphash` string/xref külön adatút; a függvényt a `0x004e62d0` és a `0x004ea360` scanner/rekordfeldolgozó út is meghívja. Ez Original/backuphash-állapot feldolgozása, nem bizonyított közvetlen UI-akció. | A közvetlen gombnyomás hipotézisét a két scanner-hívó cáfolja: az esemény háttérbeli rekordfrissítés közben is létrejön. Konkrét felhasználói kiváltó és albumtagság: **NINCS MEG**. |

**A két független út mérlege.** Az A út minden hívónál a helyi utasításokból olvassa ki az eseményrekord címét, a hívás előtti előkészítést és a dispatch feltételét. A B út a scanner vtable/xref, a külön helper stringjei, illetve az iPhoto és CThumbUI xref/string kapcsolatai alapján azonosítja a műveletcsaládot. A két út a fenti, tág műveletcsaládokban egyezik. Nem azonosítja az események pontos kódjait vagy a `]updated` tagságát; ezért a hat sor nem „megerősített”.

**A PicasaPy hétnapos szűrője.** A `recently_updated_photos()` a `time.time() - 7 * 86400` küszöböt nanoszekundumban számolja, majd `p.mtime_ns > cutoff` feltételt használ (`src/picasapy/index/queries.py:211-228`). A `mtime_ns` értéket a bejáró közvetlenül a fájl `DirEntry.stat().st_mtime_ns` mezőjéből tölti (`src/picasapy/scanner/walker.py:498-510`), az upsert pedig ezt a mezőt frissíti (`src/picasapy/index/sync_photos.py:47-52`). Ez a fájlrendszer módosítási ideje. *(Helyesbítés: a #6884 óta a kulcs sorrendje kézi dátum, EXIF felvételi dátum, ezek hiányában a fájlidő; a Colab job-650 és job-652 mérése igazolta, hogy az eredetiben a régi EXIF-dátumú, friss fájlidejű kép kimarad.)*

Az eredeti Picasa a `0x0055ece0` hétnapos kapujában a descriptor első FILETIME-párját vizsgálja. A pár a rekord építésekor `ftLastWriteTime`-ból indul, de a sikeres `0x37` EXIF `DateTimeOriginal` út felülírhatja. A `0x004ef3c0` és `0x004ef5a0` dátumállító út szintén módosíthatja az első párt (`pmp-database.md` 15.1; `0x004ef666`, `0x004ef66e`). A kezdeti és a metaadat-író bináris út a 38.2.121/a és 38.2.123 pontban van dokumentálva (`0x0040f980`, `0x004e753f`-`0x004e756a`, `0x00427844`, `0x004eeb10`). A PicasaPy e szűrője nem használja a `taken_at` vagy `taken_at_override` mezőt, csak a fájl `st_mtime_ns` értékét. Tehát ha az eredeti első FILETIME-párja eltér a fájl aktuális `st_mtime` értékétől, a PicasaPy és az eredeti eltérő dátumot használhat a hétnapos tagsági döntéshez. Az eltérés bináris és forráskód-olvasással igazolt; a mintafájlok konkrét tagsági különbsége **NINCS MEG**.

**Globális cáfoló kör.** Azt a feltételezést próbáltam cáfolni, hogy a `0x004e87c0` bármely hívása automatikusan `]updated` tagságot jelent. A `0x004e87c0` dispatcher kapui és a `0x0055ece0` descriptor-, dátum- és korlátellenőrzése külön feldolgozási lépések; a hat esemény futásidejű bemeneteit és a DBLoader döntését nem mértük együtt. A hívások megléte tehát az értesítést bizonyítja, az albumtagságot nem. A dátumra vonatkozó cáfoló próba az „eredeti mindig fájl-módosítási időt használ” feltevés volt: a `0x37` metaadatút első FILETIME-párra írása ezt cáfolja.

| Állítás | Forrás |
|---|---|
| A `0x004e87c0` hat vizsgált hívójának és hívási helyeinek címe | bináris (`0x004e7941`, `0x004e969f`, `0x004e975b`, `0x004ebce1`, `0x004f942b`, `0x00504659`, `0x00504ac8`, `0x00508843`), valamint binary-index `xrefs` |
| A `0x004e9400`-hoz kötött scanner-vtable út | bináris (`0x00c86be0`, `0x004ebff0`, `0x004e9400`) |
| A sidecar/Originals helper szövegei | bináris (`0x00501570`, `.picasaoriginals`, `Originals`, `.picasa.ini`, `Picasa.ini`) |
| A render/screenshot/view út szövegei | bináris (`CThumbDB::vftable` `0x00c821a0`, tag `0x0042e110`; `render:%d`; `0x004f92c0`, `0x0053de70`, `0x0057d080`; `CThumbUI::screensaved`, `CThumbUI::clickview`) |
| Az iPhoto beolvasási út | bináris (`0x00505030`, `iPhotoSupportEnabled`, `AlbumData.xml`, `Previews`, `Thumbnails`) |
| A backuphash-feldolgozási ág | bináris (`0x00507f60`, `backuphash`; hívók `0x004e62d0`, `0x004ea360`) |
| PicasaPy hétnapos küszöbe és mezője | forráskód (`src/picasapy/index/queries.py:218-228`, `src/picasapy/scanner/walker.py:498-510`) |
| Az eredeti dátummező első értéke és `DateTimeOriginal` felülírása | bináris (`0x0040f980`, `0x004e753f`-`0x004e756a`, `0x00427844`, `0x004eeb10`; 38.2.121/a, 38.2.123) |
| A hat hívás bármelyikéből ténylegesen bekerülő kép és pontos felhasználói művelet | **NINCS MEG** |

**A #6532 „Kész, ha” mérlege.** ✅ Az eredeti videók a 38.2.101 és 38.2.104 pontban dokumentáltak. ⛔ A teljes viselkedés bináris igazolása még nem teljes: a hat út eseménytagja és albumtagsági hatása **NINCS MEG**. ⛔ A PicasaPy összevetés ezen a körön a Recently Updated hétnapos dátumkulcsára terjedt ki; a teljes Időrend minden korábbi pontja nem lett újra végigellenőrizve. ✅ A #6713 megvalósítási jegy létezését a feladatátadás állítja, itt GitHubon nem ellenőriztem. ⛔ A kiadási összehasonlító videó vagy képsor e körben nem készült és nem igazolt.

**Javasolt megvalósítási jegybővítés.** E körből a PicasaPy szűrőjének dátumkulcs-eltérése ad konkrét fejlesztési igényt; az eseményútvonalakból egyelőre nem szabad automatikus hozzáadást előírni.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A hétnapos kapu a descriptor első FILETIME-párját olvassa; ez induláskor `ftLastWriteTime`, sikeres `0x37` olvasáskor `DateTimeOriginal` lehet, és a `0x004ef3c0`/`0x004ef5a0` dátumállító utak is módosíthatják. | A hétnapos SQL-kapu kizárólag `photos.mtime_ns`-t, azaz fájlrendszer `st_mtime_ns`-t használja. | A kapunak a Picasa-val egyező első FILETIME-pár értékét kell használnia, és a fájlrendszer `mtime_ns`-t meg kell őriznie változásérzékelésre. A megfeleltetésben kezeld a bizonyított `0x37` és `0x004ef3c0`/`0x004ef5a0` írókat; `taken_at` és `taken_at_override` közül csak azt használd, amelynek az eredeti mezővel való megfeleltetése igazolt. Rögzítsd a dátumkonverziót, és adj regressziós esetet mindkét irányú eltérésre (friss EXIF/régi fájlidő és régi EXIF/friss fájlidő), a dátumállító műveletre és EXIF nélküli fájlra. |

**Nyitott.** A pontosabb felhasználói művelet és a Recently Updated tagság eldöntéséhez a Colab mérésben a `0x004e87c0` eseményrekordot és a `0x0055ece0` DBLoader eredményét kell ugyanarra a képazonosítóra naplózni, külön vezérelt scanner-, sidecar-, render/screenshot-, iPhoto- és backuphash-műveletek után. A hat hívó mindegyikénél a stack-rekord teljes mezőjelentése és a futásidejű tagsági hatás **NINCS MEG**. A releváns függvények dekompilációja már elérhető, ezért ehhez a kérdéshez új Ghidra-kérést nem adtam ki.

##### 38.2.121/d A DateTimeOriginal írása a Recently Updated kapuja előtt (#6532, 2026-11-13)

**Kérdés és döntés.** A Picasa 3.9.141.259 helyi binárisa (SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`) a frissen felvett fájl scanner-időbélyegét először rekordba teszi, de a DBLoader a `0x37` metaadat sikeres olvasásakor a `DateTimeOriginal` értéket még a hétnapos kapu előtt az első dátumpárra írja. Így egy érvényes, 7 napnál régebbi `DateTimeOriginal`-lal rendelkező, friss mtime-ú JPEG a kapunál régi dátumot kap, és kimarad a Recently Updated albumból, ha az esemény eljut a DBLoaderig. Ez a kódsorrend binárisból megerősített; a konkrét Colab-tagságmérés még nem történt meg.

**A normál újrekord-út sorrendje.** A `0x004e62d0` a fájlnév szerinti keresésnél új rekordot épít, ha a `0x004ed7d0` nem talál meglévő indexet. A scanner rekord `+0x21c/+0x220` párját a `0x004e753f-0x004e7545` olvassa, és a `0x004e756a` a `0x0040f980` rekordépítőnek adja át. Az építő ugyanazt a 8 bájtos értéket másolja a rekord `+4/+8` és `+0xc/+0x10` időpárjába (`0x0040f9b6-0x0040f9db`). A rekordépítés után a scanner a `0x004e7941` címen átadja a helyi eseményrekordot a `0x004e87c0` dispatchernek.

Ha a dispatcher átengedi az eseményt, a DBLoader `0x0055ece0` fut le. A `0x0055ef15` a `0x00425f60` feldolgozót hívja `param_3 = 1` értékkel. A feldolgozó `0x00427844` címen beállítja a `0x37` kulcsot, a `0x00427860` címen meghívja a `0x009f05c0` metaadat-olvasót, majd sikeres olvasásnál a `0x0098bc10` dátumkonvertert. Ha mindkettő sikeres, a `0x00427898` meghívja a `0x004eeb10` írót. Az író az indexelt rekord címéhez 4-et ad (`0x004eeb6d-0x004eeb86` és `0x004eeba4`), majd a konvertált 8 bájtos értéket oda írja (`0x004eebad`). Ez az első pár `+4/+8` mezője.

A `0x0055ece0` csak a `0x00425f60` visszatérése után hívja a rekordmásolót (`0x0055f064-0x0055f074`); ezt követően a `0x0055f093-0x0055f099` az első párból képez dátumot, a `0x0055f0a1-0x0055f0b3` pedig a hétnapos határral hasonlítja össze. A kapu tehát a sikeresen beolvasott `DateTimeOriginal` értéket látja, nem az építéskori mtime-ot.

**A `0x37` jelentése és kihagyó feltételei.** A `0x00c788d8` metaadattábla-sor a `0x9003` EXIF-tagot ASCII, 20 bájtos szövegként azonosítja; a `BinaryMetadata` kulcstérben ennek kulcsa `0x37`, vagyis `DateTimeOriginal` (lásd a [`picasa-metaadat-tulajdonsagok.md`](picasa-metaadat-tulajdonsagok.md) 2-3. szakaszát). A parser a `YYYY:MM:DD HH:MM:SS` alakot olvassa (`0x0098cfe0`), és hibát ad más formátumra. Hiányzó kulcsnál vagy értéknél a `0x009f05c0` hibával tér vissza; hibás vagy elutasított dátumnál a `0x0098bc10` nem nulla értéke a `0x00427886` ágon kihagyja az írót. Ezek a közvetlenül igazolt feltételek. A `0x00427835-0x00427850` közötti `0x00421bf0` hívás eredménye csak egy helyi jelzőbe kerül, és nem kerülőág a `0x37` olvasása előtt. A vizsgált íróblokkban sem beállítást, sem fájlkiterjesztést nem vizsgál a kód.

Külső kapuk ettől még vannak. A `0x004e87c0` előbb a bemeneti objektum `+4` virtuális lekérdezését ellenőrzi, majd a rekord `+0x18` mezőjének `1` vagy `0x19` értékét követeli meg (`0x004e87c0-0x004e87f5`). A DBLoader `0x0055ece0` ezen felül a `0x00456610` előkapu 0-s eredményét igényli (`0x0055eef4-0x0055ef15`). A meglévő `0x004e62d0` dekompiláció az új scanner-rekordhoz a scanner `+0x228` mezőjét adja eseménytípusként, de nem bizonyítja ennek értékét egy új JPEG esetében. E pontos eseményérték és a dispatcher elfogadási feltételéhez való kapcsolata **NINCS MEG**. A `0x0055ece0` a dátumkonverziót a rekord négy kódjánál kihagyja: `0x15`, `0x18`, `0x17`, `0x1a` (`0x0055f07f-0x0055f091`); ezeknek a kódoknak a normál JPEG útjával való megfeleltetése itt **NINCS MEG**. A `0x37` író feltételeit és a kapu sorrendjét ez nem változtatja meg, de a teljes fájltípus-tagság állítását korlátozza.

**Két független út.** A út a vezérlési sorrend: a `0x004e62d0` létrehozza az új rekordot, a `0x004e7941` dispatch-el, a `0x0055ece0` meghívja a `0x00425f60`-t, majd később olvassa ki és hasonlítja a dátumpárt. B út az adatok azonossága: a `0x0040f980` az építéskori időt mindkét párba másolja; a külön `0x004eeb10` író az indexelt rekord `+4` címét változtatja; a `0x004edf60` mindkét párt visszaadja, a hétnapos kapu pedig a kimenet `+4` párját konvertálja (`0x0055f093-0x0055f099`). A `0x00c788d8` metaadattábla és a kulcstér külön azonosítja, hogy a `0x37` DateTimeOriginal. A két út ugyanarra a mezőre és sorrendre jut.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a kapu előtt EXIF-dátum kerül az első párba. Az építő valóban scanner-idővel indul, de a DBLoader hívási sorrendje a `0x00427898` írást a `0x0055f074` rekordmásolás elé teszi. Azt is vizsgáltam, hogy a dátumírást valamilyen beállítás vagy fájlkiterjesztés feltétel kapuzza-e: a writer blokk közvetlen vezérlési feltétele a kulcs sikeres olvasása és a dátum sikeres konvertálása; a `0x00421bf0` eredménye nem ugrik át rajta. A cáfoló próba viszont talált ellenpéldát az általános „mindig EXIF” változatra: hiányzó vagy hibás `0x37` esetén az író kimarad. A dispatcher eseménykódjának JPEG-re vonatkozó értékét a meglévő kimenet nem dönti el, ezért a minden új JPEG-re kiterjesztett állítás nem megerősített.

**Mérhető Colab-jóslat.** Egy friss, kis katalógusban minden tesztfájl mtime-ja legyen 7 napon belüli, és a `0x004e87c0` esemény, valamint a DBLoader előkapuja engedje tovább őket. Más feltételek változtatása nélkül: az érvényes, 7 napnál régebbi `DateTimeOriginal`-t tartalmazó új JPEG nem jelenik meg a Recently Updated albumban; az érvényes, 7 napon belüli `DateTimeOriginal`-t tartalmazó kontroll-JPEG megjelenik. A hiányzó vagy formátumhibás `DateTimeOriginal`-t tartalmazó kontrollnál a scanner-idő marad az első párban, így a friss mtime a dátumkapun átengedi. A mérést a fájlazonosító, a `0x004e87c0` eseményértéke, a DBLoader kapudöntése és a látható albumtagság együttes rögzítésével kell elvégezni.

| Állítás | Forrás |
|---|---|
| Új rekord kezdeti időpárja a scanner `+0x21c/+0x220` mezőjéből jön | bináris (`0x004e753f-0x004e756a`, `0x0040f9b6-0x0040f9db`) |
| A `0x37` kulcs EXIF `0x9003` DateTimeOriginal, ASCII 20 bájt | bináris (`0x00c788d8`), kulcstér: `picasa-metaadat-tulajdonsagok.md` 2-3. szakasz |
| Sikeres `0x37` olvasás és dátumkonverzió az első párt a kapu előtt felülírja | bináris (`0x00427844-0x00427898`, `0x004eeb10`, `0x0055ef15`, `0x0055f064-0x0055f0b3`) |
| Hiányzó vagy hibás `0x37` esetén az író kimarad | bináris (`0x009f05c0`, `0x0098bc10`, `0x00427865-0x00427886`) |
| Új JPEG eseményének konkrét `+0x18` értéke és DBLoader-kapuja | **NINCS MEG** |
| Régi EXIF-idős, friss mtime-ú konkrét JPEG látható albumtagsága | mérés: **NINCS MEG**, lásd Colab-jóslat |

**PicasaPy-összevetés.** A PicasaPy `recently_updated_photos()` lekérdezése a fájlrendszeri `mtime_ns` értéket veti össze a hétnapos küszöbbel; a scanner ezt a `DirEntry.stat().st_mtime_ns` mezőjéből tölti (`src/picasapy/index/queries.py:211-228`, `src/picasapy/scanner/walker.py:498-510`). Így a fenti régi EXIF / friss mtime esetben a PicasaPy beengedi a képet, míg az eredeti Picasa elfogadott DBLoader-útja a kép felvételi dátumát vizsgálja és kizárja.

**A #6532 „Kész, ha” pontjai ebből az alpontból.** ⛔ Az eredeti Időrend-videó a korábbi 38.2.101 és 38.2.104 pontokban szerepel; ebben a körben új videó nem készült. ⛔ A teljes Időrend minden látható részének bináris visszafejtése és teljes Eredeti / PicasaPy / teendő összevetése nincs lezárva. ✅ Ez a hétnapos dátummező és a `0x37` író kapu előtti sorrendjét két úton dokumentálja. ✅ A Colab-jóslat számszerűen ellenőrizhető, de a mérés még hiányzik. ⛔ A kiadási összehasonlító videó/képsor ebben a körben nem készült. A #6713 megvalósítási jegy meglétét a feladatátadás közli; a GitHubon való állapotát nem ellenőriztem.

**A #6713 jegyhez javasolt pontos bővítés.**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A friss rekord scanner-idővel indul; ha a `0x37` DateTimeOriginal olvasható és konvertálható, ez a dátum a `]updated` hétnapos kapuja előtt felülírja az első párt. Régi EXIF-dátumnál a friss fájl kizáródik. | A PicasaPy szűrője `mtime_ns`-t használ, ezért ugyanez a friss fájl bekerül. | A Recently Updated dátumkulcsát igazítsd az eredetihez: érvényes DateTimeOriginal esetén a felvétel dátumát használd, hiányzó vagy elutasított EXIF-dátumnál a fájl mtime-ját. A változásérzékeléshez őrizd meg a `mtime_ns` mezőt. Adj regressziós esetet régi EXIF + friss mtime, friss EXIF + friss mtime, valamint hiányzó/hibás EXIF esetére; az elsőnek ki, a másik kettőnek be kell kerülnie a hétnapos listába. A pontos eseménytípus-kaput a Colab-mérés előtt ne építsd bele feltételezésként. |

**Nyitott.**

- Ghidra-kör kell: 0x004e62d0 - a meglévő dekompiláció a `+0x228` értéket átadja eseménytípusnak, de nem határozza meg, hogy egy új, normál JPEG konkrétan `1` vagy `0x19` eseményt hoz-e létre, és átjut-e a `0x004e87c0` dispatcher kapuján [blokkoló]
- Ghidra-kör kell: 0x0055ece0 - a meglévő dekompiláció megmutatja, hogy a `0x15`, `0x18`, `0x17`, `0x1a` kódoknál a dátumkapu kimarad, de nem rendeli ezeket a kódokat a felismert JPEG típushoz; a `0x004edf60` descriptor mezőjének pontos típusjelentése mi, és a JPEG út kódja mi? [blokkoló]
- Futásmérés kell a fenti Colab-jóslat tényleges albumtagságához és a közvetlenül látható eredményhez.

##### 38.2.121/e A `]updated` token és a CAlbumState sorának kapcsolata (#6532, 2026-11-13)

**Kérdés és eredmény.** A `]updated` nem egy forráskódban rögzített sorszámot kap. A `CThumbDB+0x48` tokenvektorában elfoglalt futásidejű ordinalja azonosítja a `CAlbumState+0x138` tömb azon sorát: ha a token az ordinal `i` helyen van, az Időrend állapotfrissítője a `+0x24*i` sort kezeli. A `]updated` konkrét numerikus ordinalja **NINCS MEG**, mert a tokenvektort a program futás közben tölti.

**A út: tokenregisztráció és Időrend-frissítés.** A `0x004abe70` a `0x00c8334c` című `]updated` stringet adja a `0x004ad220` függvénynek (`0x004ac552`-`0x004ac558`). A `0x004ad220` az állapot `[+0xc4]` CThumbDB objektumának `+0x48` alobjektumán hívja a vtable `+0x34` helyét (`0x004ad231`-`0x004ad251`). A `0x00415790` konstruktor ezt az alobjektumot a `0x00c81fa4` vtáblához köti (`0x00415804`); a `Picasa3.exe` nyers `.rdata` adataiban a tábla `+0x34` slotja `0x00475c30`.

A `0x00475c30` a kapott stringet a `0x00494750` keresőnek adja, és az eredmény ordinalját kiírja a kimeneti címre (`0x00475c5b`-`0x00475c80`). A kereső a `CThumbDB+0x48` alobjektum `+0xb00` tokenvektorában ellenőrzi az egyező stringet, és annak indexét adja vissza (`0x0049479b`-`0x00494821`, `0x004948a2`-`0x004949d9`); hiány esetén `-1` marad.

**B út: az ordinal visszakeresése az Időrend-frissítőből.** A `0x004aae90` a `CAlbumState+0x138` tömböt `0x24` bájtos sorokkal járja be. A sor `i` `+0x0c` állapotát olvasva ugyanazt az `i` értéket adja a `0x004b0190`-nek (`0x004ab2a0`-`0x004ab2a6`, `0x004ab34a`-`0x004ab359`). A `0x004b0190` a `CThumbDB+0x48` vtable `+0x2c` helyét hívja (`0x004b01dd`-`0x004b01f2`); a nyers `.rdata` slotérték `0x004406f0`. Ez a függvény az `i` ordinaldal ugyanennek az alobjektumnak a `+0xb00` tokenvektorából olvas stringet, majd annak `CSlice` posting listáját kéri le (`0x0044079e`-`0x004407b9`, `0x004408ed`-`0x004408ef`). Így a `CAlbumState` `i` sora a vektor `i` tokenjének feldolgozási állapota; a `]updated` sora az a `i`, ahol a vektor eleme `]updated`.

**A `+0x0c == 2` feltétele.** A `0x004aae90` ezen az úton csak a `+0x0c == 1` sorokat vizsgálja tovább (`0x004ab31d`-`0x004ab33b`). Ha a `0x004b0190(i)` eredménye nem nulla, a 2-es állapot írása kimarad (`0x004ab359`-`0x004ab360`). Nulla eredménynél a függvény minden ágon meghívja a `0x004ab520(state,i,2)` írót; az egyik ágon a sor `+0x14` mezőjét is `1`-re állítja, a másikon a `0x006c9d60` eredményét írja oda (`0x004ab455`-`0x004ab49b`). A `0x004ab520` közvetlenül a `[state+0x138+i*0x24+0x0c]` címre írja az átadott `2` értéket (`0x004ab570`-`0x004ab57d`). A `+0x18`, `+0x19`, illetve a helyi descriptor-flag feltételek csak azt döntik el, melyik `+0x14` ág fut; a `+0x0c` 2-es írását nem zárják ki.

A `0x004406f0` a `CSlice+0x64` posting-lista meglétét és pozitív elemszámát is ellenőrzi. Üres vagy hiányzó lista esetén `-1`-et ad; nem üres lista esetén a sikeres lekérés értéke `0` (`0x00440967`-`0x00440a41`, `0x00440a7a`-`0x00440adf`). Ezért a vizsgált frissítő körben a sor csak akkor jut `+0x0c == 2` állapotba, ha már `1` állapotú, és a tokenhez legalább egy indexelt posting-listaelem tartozik.

**Független listaépítő kontroll.** A `0x004b8470` egy másik útból ad ordinalt a `0x004b29d0`-nak (`0x004b85c1`-`0x004b85c8`). A `0x004b29d0` közvetlenül a `CAlbumState+0x138+i*0x24+0x0c` mezőt olvassa, és csak `2` esetén folytatja a sor felvételét a saját `+0x158` listájába; eltérő állapotnál korán visszatér (`0x004b29d0`, meglévő Ghidra-kimenet: `2026-11-10-6532-colab-decomp.txt`). Ez a külön fogyasztó út megerősíti, hogy a 2-es állapot az adott ordinal kész sorát jelöli. Független adatkontrollként a bináris `.rdata` vtáblája `+0x2c -> 0x004406f0` és `+0x34 -> 0x00475c30` értékeket tartalmaz, a konstruktor pedig ugyanazt a táblát állítja be a `CThumbDB+0x48` alobjektumhoz.

**Cáfoló kísérlet.** Azt a feltevést próbáltam cáfolni, hogy a `]updated` token puszta jelenléte elég a `+0x0c == 2` állapothoz. A `0x004406f0` tokenhez tartozó üres posting listánál `-1`-et ad, miközben a `0x004aae90` kizárólag `0` visszatéréskor hívja a 2-es állapot írót. A próba tehát cáfolta a puszta regisztráció elégségességét. Az eredményt ugyanazzal az utasításszintű mércével ellenőriztem a teljes `0x004406f0` visszatérési útban, a hívó állapotkapujában és a `0x004ab520` közvetlen írásában; ezek egyeznek. A `paszta.memoria_kapu()` első műveletként hívott teljes `.text`-pásztázása 2 884 879 utasítást dolgozott fel; visszaadta a `0x004ad24b` `+0x34` vtable-olvasás és hívásablakát, a `0x004b01e3` `+0x2c` vtable-olvasás és hívásablakát, valamint a `0x004aaed9` pozitív kontrollt. Az xref-index negatív eredményét nem használtam bizonyítékként.

**Mit jelent a bal hasábban való megjelenésre.** A `0x004b8470`-`0x004b29d0` listaépítő útba a `]updated` sora csak a 2-es, feldolgozható állapotban kerül be; a fenti bináris feltétel szerint ez legalább egy indexelt találatot igényel. A korábbi Colab-mérésben a `Recently Updated (24)` sor látszott, 24 képpel (viselkedési spec 38.2.121/c, Colab #545-#550). A tényleges üres, nulla elemű album bal hasábban való láthatóságát nem mértük, és a `+0x158` belső lista UI-hoz kötése ezen a körön nem lett végigkövetve, ezért a „csak nem üresen látszik” felhasználói állítás **NINCS MEG**.

**PicasaPy-összevetés.** A PicasaPy `AlbumsSection.qml` sora `!section.collapsed` feltétellel látható, a számlálóértékétől függetlenül (`src/picasapy/app/qml/PicasaPy/AlbumsSection.qml:142-160`); a countot a `count_recently_updated_photos()` adja (`src/picasapy/app/controller_photo_list_mixin.py:196`). A PicasaPy forrása tehát nulla találatnál is kirajzolja a `Recently Updated (0)` sort. Ez lehetséges megjelenítési eltérés, de mivel az eredeti Picasa nulla elemszámú bal hasábját nem mértük, ebből most nem következik igazolt fejlesztési hiba.

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| A `]updated` a `CThumbDB+0x48` tokenvektorának futásidejű ordinaljához kötődik; a hozzá tartozó `CAlbumState+0x138` sor azonos ordinalú. | bináris (`0x004abe70`, `0x004ad220`, `0x00475c30`, `0x00494750`, `0x004aae90`, `0x004b0190`, `0x004406f0`; `.rdata` `0x00c81fa4`) | megerősített a képletre; a konkrét szám **NINCS MEG** |
| A `+0x0c` állapot ezen a frissítő úton `1`-ből `2`-be vált, ha a `0x004b0190(i)` eredménye `0`, és a beállító függvény a `2` állandót írja. | bináris (`0x004aae90`, `0x004ab520`, `0x004406f0`) | megerősített |
| A sikeres nulla eredményhez nem üres `CSlice+0x64` posting lista kell. | bináris (`0x004406f0`, `0x00440967`-`0x00440a41`, `0x00440a7a`-`0x00440adf`) | megerősített |
| A `Recently Updated (24)` sor látszott a 24 képes mérési katalógusban. | mérés (Colab #545-#550, viselkedési spec 38.2.121/c) | megerősített |
| Az eredeti Picasa nulla elemszámú sora látható-e a bal hasábban. | **NINCS MEG**; Colab-mérés kell üres, de indexelt katalógussal | nyitott |
| A PicasaPy QML a sort nulla számláló mellett is kirajzolja. | forráskód (`AlbumsSection.qml:142-160`, számláló: `controller_photo_list_mixin.py:196`) | megerősített |

**A #6532 „Kész, ha” pontjainak állása.** ✅ E körben a `]updated` token sorszáma és a `CAlbumState+0x138` sorindexének kapcsolata binárisból igazolt. ⛔ A konkrét futásidejű ordinal és az eredeti nulla elemszámú bal hasáb láthatósága **NINCS MEG**. ⛔ A teljes Időrend minden látható részének specifikációja továbbra is tartalmaz nyitott pontokat; az üres állapot vizuális mérése hiányzik. ⛔ A teljes eredeti/PicasaPy összevetés és a kiadási videó vagy képsor nincs lezárva. ✅ Az eredeti felvételekre a korábbi 38.2.101 és 38.2.104 pont hivatkozik; ebben a körben új videó nem készült. A #6713 nyitott GitHub-állapotát hálózat nélkül nem ellenőriztem.

**Nyitott.**

- Futásmérés kell: ugyanabban a Picasa 3.9 folyamatban rögzítsd a `CThumbDB+0x48+0xb00` tokenvektorban a `]updated` ordinalját és a `CAlbumState+0x138` sorokat; ez adja a konkrét numerikus sort.
- Futásmérés kell: üres, de érvényes katalógusban figyeld meg, hogy a `Recently Updated` sor megmarad-e a bal hasábban. A kód a belső lista státuszkapuját bizonyítja, a widget láthatóságát közvetlenül nem.

**Végső következtetés a bal hasábhoz.** Az eredeti Picasa binárisa azt bizonyítja, hogy a `]updated` token sora a belső kész listába csak nem üres posting listával kerülhet be. A korábbi, 24 képes mérésben a sor látszott; a nulla elemszámú eredeti UI-eset **NINCS MEG**. A PicasaPy ezzel szemben a sort nulla találatnál is megjeleníti, így az üres állapotban lehetséges UI-eltérés van, de ennek javítását az eredeti nulla elemszámú viselkedés mérése előtt nem támasztja alá bizonyíték.

##### 38.2.121/f A `Recently Updated` sor üres állapotának CAlbumList-kapuja (#6532, 2026-11-13)

**Kérdés és eredmény.** Ha a `]updated` album posting listája üres, megjelenik-e a sora az eredeti Picasa bal hasábjában? A vizsgált bináris út alapján **nem**: az üres posting lista nem állítja a tokenhez tartozó `CAlbumState` sort kész (`2`) állapotba, így a sor nem kerül a megjelenített listába. A `CAlbumList` sorrajzolója ezt a listát használja, és nem rajzol a lista elemszámán kívüli indexet. Ez a statikus döntés megerősített; a nulla elemszámú képernyő Colab-mérése még hiányzik. Ez a pont pontosítja a 38.2.121/e korábbi, UI-hídra vonatkozó **NINCS MEG** megállapítását.

**A út, a sor felvétele.** A `0x00c8334c` string_xrefs-bejegyzés `]updated` szövegét a `0x004abe70` regisztrálja; a `0x00c83358` a `Recently Updated` feliratot tartalmazza, szintén a `0x004abe70` hivatkozásával. A token futásidejű ordinalja a `CAlbumState+0x138` megfelelő, `0x24` bájtos sorára mutat (38.2.121/e). A `0x004aae90` csak akkor írja a sor `+0x0c` mezőjébe a `2` állapotot, ha a `0x004b0190` lekérdezés `0` értékkel tér vissza. A `0x004406f0` hiányzó vagy üres posting listánál `-1`-et ad, ezért nulla `]updated` elem esetén az állapot nem lesz `2`. A `0x004b8470` a megjelenítési rekordokat építi: az opcionális `+0x9d` albumtípus-szűrőn átengedett ordinalokhoz hívja a `0x004b29d0`-t. Ez utóbbi a `+0x0c == 2` feltétel hiányában korán visszatér, és nem növeli a `CAlbumState+0x158` lista `+0x15c` darabszámát. További szűrők ezt a sort még kizárhatják, de az üres tokenhez nem hoznak létre pótsort.

**B út, a bal hasáb rajzolása.** A binary-index RTTI-táblája a `0x00cb2898` címet `CAlbumList::vftable`-ként, a `0x00762540`, `0x00763150`, `0x007623b0` belépőkkel azonosítja. A `0x004039f0` a CThumbUI-konstruktort (`0x005643e0`) hívja, majd a létrejött pointert adja a `0x0040bf70`-nek. Ez a függvény ugyanazt a pointert adja a `0x00565920`-nak; az utóbbi lefoglalja a `CAlbumList` objektumot, amelynek konstruktora `0x00761870` a szülő pointerét a `CAlbumList+0x24` mezőbe, a vtable-t pedig a `+0x0` mezőbe írja. A CThumbUI `+0x2c0` mezője `CAlbumState` (38.2.69, konstruktor- és RTTI-út). A `0x00763150` a `CAlbumList+0x24` szülőn át ebből olvassa a `CAlbumState+0x15c` kódolt elemszámot, majd `>> 1` értékkel képezi a megengedett sorok számát. A kért sorindexet ehhez hasonlítja; `darabszám <= index` esetén a `0x00765cf6` epilógushoz ugrik, amely nullát ad vissza. Érvényes indexnél csak ezután jut a soradat lekérdezéséhez (`0x004ae4e0`, `0x004b0190`). Így a `]updated` sor csak a `0x004b8470` által felvett rekordként rajzolódhat ki; nincs külön CAlbumList-pótsor.

**Szűrők és beállítások.** A `0x00761870` a `0x00c8fd14` string_xrefs-bejegyzésű `ShowAlbumThumbnails2` preferenciát a `CAlbumList+0x20` mezőbe olvassa. A rajzoló (`0x00763150`) ezt a byte-ot beolvassa, de a lista elemszámának kapuját nem erre ágaztatja. A `CAlbumState+0x9d` másik szűrője a `0x00c8fd88` című `thumbui/folderview` beállítástól függ (`0x005db823`); a listaépítő albumtípus szerint szűrhet vele (`0x004b8470` → `0x004461a0`). Ez a típus-szűrés további sorokat kivehet, de üres `]updated` posting listából sort nem készíthet. A vizsgált CAlbumList-felvételi útban külön `]updated` rejtési jelzőt nem találtam; a szükséges felvételi feltétel a kész állapot és a sor tényleges felvétele. A két beállítás futásidejű értéke **NINCS MEG**, de a nulla elemű sor hiányát ez nem változtatja meg.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a különleges album üresen is rögzített sor. A CAlbumList konstruktora valóban betölti a `0x00ca2d88` című `icons/special_album` erőforrást, de ez önmagában csak ikonerőforrás. A cáfoló ellenőrzésben a `0x00763150` vtable-rajzoló útját a teljes `CAlbumState+0x15c` indexkaputól a soradat-lekérdezésig követtem; a határvizsgálat a soradat és a kép rajzolása előtt fut, és nincs benne a `]updated`-nek külön ága. A `0x004b29d0` külön, sorfelvételi útján ugyancsak közvetlenül visszatér, ha az állapot nem `2`. A két független ellenőrzés tehát cáfolja a fix, elemszámtól független CAlbumList-sor lehetőségét. A `paszta.memoria_kapu()` első műveletként futó teljes `.text`-pásztázása 2 884 879 utasítást dolgozott fel; a CAlbumList-vtable címét csak a `0x00761896` konstruktorbeli vtable-beállításként találta. Az index negatív találatát nem használtam bizonyítékként.

**A két független út.** A út a token posting listájától az állapotfrissítőn, majd a kész sorokat építő `0x004b8470`/`0x004b29d0` páron át bizonyítja, hogy üres tokenhez nem készül megjelenítési rekord. B út a CAlbumList vtable- és szülőpointer-adatútján át bizonyítja, hogy a bal hasáb rajzolója ugyanezen CAlbumState darabszámával indexeli a sorokat, és elutasítja az elemszámon kívüli sort. Mindkét út ugyanarra az eredményre jut: a nulla elemű `]updated` sor nem jelenik meg a vizsgált bal oldali albumlistában.

**PicasaPy-összevetés.** A PicasaPy kibontott Albums szekciója a sort `visible: !section.collapsed` feltétellel mutatja, a számlálótól függetlenül (`src/picasapy/app/qml/PicasaPy/AlbumsSection.qml:142-160`); a számláló forrása `count_recently_updated_photos()` (`src/picasapy/app/controller_photo_list_mixin.py:196`). Nulla találatnál ezért a kibontott PicasaPy szekcióban `Recently Updated (0)` látható, míg az eredeti listában a sor hiányzik.

**Colab-jóslat.** Rögzítsd az eredeti Picasa 3.9.141.259 bal hasábját olyan friss katalógus-újraolvasás után, amelyben minden kép fájlideje és, ha van, `DateTimeOriginal` értéke hét napnál régebbi; így a `0x0055ece0` kapujának használt dátumpárja is régi. Tartsd az album/folder nézet beállítását és a panel állapotát változatlanul. A jóslat szerint a `Recently Updated` sor nem jelenik meg, miközben a más albumok/mappák sorai megmaradhatnak. Kontrollként egy, a `0x0055ece0` hétnapos kapuján átjutó képnél a sor megjelenik, és `1` darabot mutat. A felvételen együtt rögzítsd a bal hasábot és a `]updated` ordinalhoz tartozó `CAlbumState+0x0c` állapotot.

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| Üres `]updated` posting lista mellett a token állapota nem jut `2`-re. | bináris (`0x004406f0`, `0x004aae90`, `0x004ab520`) | megerősített |
| A megjelenítési lista csak `+0x0c == 2` állapotú sorból bővül. | bináris (`0x004b8470`, `0x004b29d0`, `CAlbumState+0x158/+0x15c`) | megerősített |
| A CAlbumList a szülő CThumbUI `+0x2c0` CAlbumState-listájából rajzol, a kért indexet a `+0x15c >> 1` elemszámmal kapuzza. | bináris (`0x004039f0`, `0x0040bf70`, `0x00565920`, `0x00761870`, `0x00763150`, `0x00cb2898`; típus: 38.2.69) | megerősített |
| A PicasaPy kibontott Albums szekciója nulla találatnál is megjeleníti a sort. | forráskód (`AlbumsSection.qml:142-160`, `controller_photo_list_mixin.py:196`) | megerősített |
| Az eredeti, nulla elemes képernyőn a sor ténylegesen hiányzik. | mérés: **NINCS MEG**; statikus kétutas következtetés szerint hiányzik | Colab-megerősítés nyitott |
| A Colab-vezérelt katalógusban a `]updated` konkrét futásidejű ordinalja és a két beállítás értéke. | **NINCS MEG** | nyitott |

**A #6532 „Kész, ha” pontjainak állása ebből a kérdésből.** ✅ Az üres sor statikus felvételi és rajzolási szabálya két független útból igazolt. ⛔ Az üres állapotú eredeti képernyő videós mérése hiányzik; az alábbi Colab-jóslat ezt ellenőrzi. A #6532 teljes „Kész, ha” feltételei ettől még nem teljesülnek: a teljes Időrend-specifikáció, a tételes PicasaPy-összevetés és a kiadási összehasonlító anyag korábbi nyitott pontjai megmaradnak.

**Nyitott.**

- Colab-futásmérés kell: minden kép dátuma hét napnál régebbi katalógusban vedd fel a kibontott bal hasábot, majd egy friss kontrollképpel ismételd meg. Rögzítsd a `]updated` ordinalt, állapotát és a látható sorokat.
- A `thumbui/folderview` és `ShowAlbumThumbnails2` futásidejű értéke **NINCS MEG**; a statikus nulla-sor döntéshez nem szükséges, a mérést változatlan értékek mellett kell elvégezni.
- A teljes Időrend minden látható elemének visszafejtése és a kiadásba való összehasonlító videó/képsor továbbra is nyitott.

#### 38.2.124 Recently Updated: a 0x00425f60 típus-diszpécsere és a nullás visszatérés (#6532, 2026-11-13)

**Kérdés és határ.** A 38.2.121/a és 38.2.123 nyitva hagyta, hogy a `0x00425f60` mely típusoknál és feltételekkel adhat nullás EAX-ot. A vizsgált Picasa3.exe 3.9.141.259 SHA-256 értéke `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. A meglévő Ghidra-kimenetre cím szerint rákerestem a `0x00425f60` és `0x005b1570` címek használata előtt; új Ghidra-kör és futásidejű mérés nem történt.

**A hívó által vizsgált eredmény.** A `0x00425f60` a `0x004264b1` címen hívja a `0x005b1570`-et, majd annak EAX-át a `[esp+0x3c]` címre menti (`0x004264b6`). A 38.2.121/a hét kilépési pontjából csak a `0x0042663c` adhat nullát: a `0x00426571` előző sentinel-ellenőrzése után a `0x004265d1` által ellenőrzött jelző nem lehet nulla, a mentett érték pedig nem lehet `0xf4242`; a visszatérési helyreállítás a mentett EAX-ot használja (`0x00426624`). A `0x0055ece0` DBLoader a `0x00425f60` után a `0x0055ef1a` címen teszteli az EAX-ot; nem nulla értéknél a `0x0055f849` elutasító ágra ugrik. Ez az eredményfeldolgozó kapu, nem a Timeline-kártyák dátumának vagy elrendezésének leírása.

**Típus-diszpécser.** A `0x005b1570` a rekord típusából 2-t levon, majd a `0x005b1ba4` byte-táblával kiválasztja a `0x005b1b64` ugrótábla bejegyzését (`0x005b17ad-0x005b17c5`). A hívott segéd célok:

| Típusérték | Hívott segéd | Megjegyzés |
|---|---|---|
| `0x02` | `0x005ad6f0` | a `string_xrefs` ehhez a függvényhez a `Preferences` és `DeferLoadJPEG` szövegeket rendeli |
| `0x03` | `0x005ae450` | |
| `0x06` | `0x005ae300` | |
| `0x07` | `0x005ad9c0` | |
| `0x08`, `0x0a`, `0x0b`, `0x0c`, `0x1d` | `0x005aecf0` | közös ág |
| `0x09` | `0x005ae7a0` | csak ha a `0x00550c60` AL eredménye nem nulla; különben az alapérték marad |
| `0x0d` | `0x005adb30` | |
| `0x0e` | `0x005af040` | |
| `0x0f`, `0x10`, `0x11` | `0x005aeeb0` | közös ág |
| `0x12` | `0x005b0730` | a `0x005b1570` ezt követően külön ágban is folytathatja |
| `0x15`, `0x17`, `0x18`, `0x1a` | `0x005af660` | közös ág |
| `0x16` | `0x005ae610` | |
| `0x1b` | `0x005af310` | második argumentum `0` |
| `0x1c` | `0x005af310` | második argumentum `1` |
| `0x1f` | `0x005add10` | |
| a felsoroltakon kívüli érték | nincs típuság | a lokális alapérték `3` marad, kivéve a külön kezelt bemeneteket |

Az `0x00` típus a `0x00a4c140` hívás eredményére cserélődik a diszpécser előtt. A `0x04` típus a `0x005b1570` elején korán kilép, és a `0x00425f60` saját, korábbi ágában is külön kezelve van (`0x00426081-0x00426089`). A `0x12` ág segédhívás utáni feldolgozása és a közös visszatérési út feltételei továbbra is számítanak a végső EAX-hoz.

**Egy közvetlenül igazolt nullás út.** A `0x06` típus a `0x005ae300` segédet hívja. A segéd `0x005ae420` összehasonlítási ágánál, ha `EBX == ESI`, a `0x005ae43f` nullázza az EAX-ot, majd visszatér. A `0x005b1570` közös visszatérési útján a nulla lokális eredmény a `0x005b19b8-0x005b19c1` ágon EAX-ként megmarad. A gépi kód tehát ezen a típuságon nullát előállító utat mutat, amennyiben az egyenlőségi ág elérhető; az összehasonlítás operandusainak termék- vagy képformátum-jelentése, illetve a feltétel futásidejű teljesülése **NINCS MEG**.

**A közös záró ág pontos szabálya.** A típuság által beállított érték a `0x005b197d` címen kerül a közös ellenőrzésbe. Ha ez `0xf4242`, a függvény ezt az értéket adja vissza (`0x005b1980-0x005b198a`). Más értéknél meghívja a `0x00a4c6e0` és `0x00a4c0a0` segédeket. Ha a lokális eredmény nulla, vagy a második segéd AL eredménye nulla, a `0x005acf40` után a lokális eredmény kerül EAX-ba (`0x005b19a0-0x005b19c1`). Ha a lokális eredmény nem nulla és a második segéd AL eredménye nem nulla, a `0x005b1460` visszatérési EAX-a lesz az eredmény (`0x005b19a0-0x005b19b3`). Így a normál közös záró ágban a típussegéd nullája megmarad; külön nullás lehetőség a `0x005b1460` út eredménye. A `0x12` külön folytatása és a bemenet-null / `0x04` korai kilépés ezt a közös szabályt megkerüli, ezért ezek teljes kimenete külön marad nyitva.

**Két független út.**

- **A út:** a helyi utasításolvasás követi a `type - 2` indexképzést (`0x005b17b0-0x005b17c5`), a nyers PE-ben külön olvassa a `0x005b1ba4` byte-táblát és a `0x005b1b64` dword ugrótáblát, majd a célcímeknél leolvassa a helperhívásokat. Ebből áll elő a fenti típuscsoportosítás.
- **B út:** a már meglévő `2026-11-11-6532-colab-12-olvasok-hivok.txt` Ghidra-kimenet `FUN_005b1570` switch-e felsorolja a típusértékeket és a segédeket (17279-17495. sor). A dekompilált switch és az utasításokból külön kiolvasott PE-táblák ugyanazokat a hívási csoportokat adják.

A két út a diszpécser hozzárendeléseire egyezik. Nem támasztják alá önmagukban az összes segéd nullás feltételét.

**Cáfoló kísérlet.** Azt a lehetséges leegyszerűsítést próbáltam cáfolni, hogy minden típus saját, feltétel nélküli segédhívást kap. A `0x005b1ba4` és `0x005b1b64` táblái, a hívási utasítások és a Ghidra switch együttes ellenőrzése közös segédágakat mutat az `0x08/0x0a/0x0b/0x0c/0x1d`, `0x0f/0x10/0x11`, valamint `0x15/0x17/0x18/0x1a` csoportoknál. A `0x09` előfeltételes segédhívást kap; a `0x04` korán kilép; több más típus a `3` alapértéken marad. A cáfolatot ugyanazzal a két úttal ellenőriztem, és a két listázás egyezett.

**PicasaPy-összevetés.** A feltárt kód a `Recently Updated` DBLoader rekordfeldolgozási kapujához tartozik. Nem rendeli a numerikus típusokat PicasaPy fotó-, videó- vagy timeline-rekordhoz, és nem bizonyít megjelenítési eltérést a Timeline nézetben. A `src/picasapy/timeline.py:53` `resolve_date()` függvénye az EXIF `taken_at` értéket részesíti előnyben, majd a befagyasztott `sort_mtime_ns` értékre esik vissza; a `src/picasapy/timeline.py:76` adja át az indexrekord dátumát. A `src/picasapy/app/qml/PicasaPy/TimelineView.qml:133` carousel- és a `:277` csúszka-mozgást kezel. Ezeket a jelen bináris típusértékekkel nem lehet megfeleltetni. Ezért a `picasa-idorend-viselkedes.md` „Eredeti / Nálunk / Teendő” táblája ebből az eredményből nem módosul.

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| A `0x00425f60` a `0x005b1570` eredményét menti, és a `0x0055ece0` a `0x00425f60` EAX-át arra teszteli, hogy nulla-e. | bináris (`0x004264b1-0x004264b6`, `0x0055ef15-0x0055ef22`) | megerősített a hívási és kapu-utasításokra |
| A `0x005b1570` típusonkénti dispatch táblája a fenti helper-csoportokat választja. | bináris (`0x005b17ad-0x005b17c5`, tábla `0x005b1ba4`, `0x005b1b64`, segédhívások `0x005b17cc-0x005b192e`); meglévő Ghidra switch | megerősített a hozzárendelésre |
| A `0x06` dispatch-út egy feltételben nullát adhat, és a közös ág továbbadja a nullát. | bináris (`0x005ae420-0x005ae445`, `0x005b19b8-0x005b19c1`) | megerősített erre az egy útvonalra |
| A segédhívások belső nullás feltételei típusonként, a `0x005b1460` rekurzív kimenete, valamint a `0x12` és korai kilépési ágak végső EAX-a. | **NINCS MEG** | nyitott |
| A numerikus típusok emberi jelentése, és azok megfeleltetése a PicasaPy Időrend rekordsoraihoz. | **NINCS MEG** | nyitott |

**A #6532 készültsége.** ✅ A meglévő Ghidra switch és a nyers PE-ugrótáblák alapján a vizsgált típus-diszpécser hívási hozzárendelése dokumentált; a közös záró ág visszatérési formulája is megvan. ⛔ A segédhívások belső nullás feltételei, a `0x005b1460` rekurzív kimenete, valamint a `0x12` és korai kilépési ágak végső EAX-a nincs lezárva. ⛔ E kör nem állapít meg termékszintű Timeline-eltérést, ezért fejlesztési táblabővítést nem javasol. ⛔ A teljes Időrend-specifikáció, a teljes felvételi összevetés és a kiadási összehasonlító videó vagy képsor ettől továbbra is nyitott.

**Nyitott.** A következő statikus lépés mindegyik, a fenti táblában szereplő külön segédfüggvény nullás kilépéseinek feltétel szerinti követése, majd a `0x005b19a0-0x005b19c1` közös ág és a `0x005b1460` visszatérési út végigkövetése. A `0x00425f60` veremjelző `[esp+0x2fa]` íróját is vissza kell vezetni. Az `annot_disasm.py`-val rendelkezésre állnak a segédfüggvények határai; ehhez a jelenlegi kérdéshez új Ghidra-kör nem szükséges. A PicasaPy-val való fejlesztési eltérést csak akkor szabad felvenni, ha a típus numerikus értékének és a UI-rekordnak a megfeleltetése igazolt.

#### 38.2.125 Recently Updated: a nullás segédágak, a fájl-újraolvasás és a veremjelző (#6532, 2026-11-13)

**Kérdés és határ.** A 38.2.124 nyitva hagyta a `0x005b1570` típus-diszpécser segédfüggvényeinek nullás visszatérési feltételeit, a `0x005b1460` fájl-újraolvasó teljes normál visszatérési útját, a `0x12` külön ág és a korai kilépések EAX-át, valamint a `0x00425f60` `[esp+0x2fa]` jelzőjének íróját. A vizsgált Picasa3.exe 3.9.141.259 SHA-256 értéke `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. A függvénybelépők és az indexelt méretek a `functions` táblából valók; az utasításokat helyben, `annot_disasm.py`-val olvastam. A `0x005b1570` indexelt mérete 1166 bájt, de a `0x005b15fe` közvetlen ágcélja, `0x005b1b1c` a mérettartományon kívül van; ezt a külön ágcélt is dekódoltam a tényleges EAX megállapításához. A `0x005b1570` és `0x00425f60` meglévő Ghidra-kimenetét cím szerint ellenőriztem, új Ghidra-kört és futásidejű mérést nem használtam.

**A típussegédek nullás visszatérései.** Az alábbi feltételek az utasításszintű bejárásból származnak. A `megerősített` címkét csak a kétutas egyezést mutató diszpécser- és veremjelző-állításokra használom; a segédfüggvények belső nullás feltételei egyetlen helyi utasításolvasási úton állnak, ezért **feltételesek**.

| Eredeti típus / út | Nulla EAX feltétele | Bináris nyom |
|---|---|---|
| `0x02` → `0x005ad6f0` | A `0x005ad270` nulla eredménye közvetlenül nullára fut. Másik nullás ág: a `0x005ad270` nem nulla, a `[this+0xfd]`, a `DeferLoadJPEG` beállítás és a `[this+0xff]` kapu átenged (`0x005ad779`-`0x005ad802`), a `0x009d63f0` után a `[this+0xbc]` és `[this+0xc0]` mező is nem nulla. Egyébként a `0x009d5b90` eredménye jut vissza. | Eredeti: `0x005ad774`, `0x005ad802`-`0x005ad87d`, `0x005ad858`-`0x005ad87d`, `0x005ad997`-`0x005ad9aa` |
| `0x03` → `0x005ae450` | A `0x00a97640` és a `0x00a976c0` egyaránt nullát ad; a következő `0x00a978c0` eredménye nem `0xf4242` és nem `-1`. | Eredeti: `0x005ae493`-`0x005ae50c`, `0x005ae552`-`0x005ae5a1`, `0x005ae5cb`-`0x005ae608` |
| `0x06` → `0x005ae300` | A korai ágak nem nullás eredményt vagy `2`-t adnak. A fő feldolgozás a `0x00aa0f20` hívás nullás EAX-át közvetlenül visszaadja. | Eredeti: `0x005ae31e`-`0x005ae392`, `0x005ae395`-`0x005ae445` |
| `0x07` → `0x005ad9c0` | A segéd a `0x009d5b90` EAX-át adja vissza; nulla pontosan akkor, ha ez a hívás nullát ad. | Eredeti: `0x005ad997`-`0x005ad9b1` |
| `0x08`, `0x0a`, `0x0b`, `0x0c`, `0x1d` → `0x005aecf0` | Nulla lehet a `0x005ad270` nulla eredményénél; a `0x08` ágon a `0x00551f40` nullája és a `[this+0xbc]`, `[this+0xc0]` nem nulla értéke mellett; a `0x0b/0x0c` ágon a `0x00a9b320` nullájánál; vagy a közös `0x005aea90` záró hívás nullájánál. | Eredeti: `0x005aed9e`-`0x005aedb9`, `0x005aee08`-`0x005aee34`, `0x005aee5b`-`0x005aee76`, `0x005aee85`-`0x005aeea1` |
| `0x09` → `0x005ae7a0` | A diszpécser csak a `0x00550c60` igaz AL-eredményénél hívja. Ekkor a `0x005550d0` nullája a segéd további feldolgozásán át `0`-val tér vissza; nem nulla eredményét közvetlenül továbbadja. | Eredeti: `0x005b1836`-`0x005b184b`, `0x005ae80d`-`0x005ae81a`, `0x005ae993`-`0x005ae9a6`, `0x005ae9a9`-`0x005ae9c2` |
| `0x0d` → `0x005adb30` | A `0x00a4f6a0` nulla eredménye után a `0x00a4f9d0` is nulla; a `0x00a4fe30` eredménye ekkor `0xf4242` és `-1` helyett más érték. Ez utóbbi esetben a segéd nullával tér vissza. | Eredeti: `0x005adb79`-`0x005adb82`, `0x005adc1d`-`0x005adc28`, `0x005adc5e`-`0x005adce7` |
| `0x0e` → `0x005af040` | A `0x00b0dd60` és a `0x00b0e2d0` egyaránt nullát ad. | Eredeti: `0x005af095`, `0x005af140`, nulla zárás `0x005af2f9`-`0x005af2ff` |
| `0x0f`, `0x10`, `0x11` → `0x005aeeb0` | Normál befejezéskor feltétel nélkül nullát ad. | Eredeti: `0x005aeeb0` függvénytest, `0x005aefc0`-`0x005aefc6` |
| `0x12` → `0x005b0730` | A két lehetséges `0x005ad270` képkérés bármelyikének nullája a `0x005b0f86` nullás zárásra jut. A későbbi ágban a `0x008cfeb0` EAX-a legyen `0`, a `[esp+0xa8]` jelző legyen `0`, és a `[this+0xbc]`, `[this+0xc0]` méret mind legfeljebb `0x3e80`; a feldolgozás ekkor a `0x005b0f86` nullás zárásig jut. A `0x008cfeb0` `0xf4242` eredménye külön visszatérési útra vezet; a sikertelen méretkapu `3`-as ágra visz. | Eredeti: képkérések `0x005b087a`, `0x005b096f`; kapuk `0x005b0986`, `0x005b0d59`-`0x005b0dd4`; nulla `0x005b0f86`-`0x005b0f9c`; `3` `0x005b0fd5`-`0x005b0fe2` |
| `0x15`, `0x17`, `0x18`, `0x1a` → `0x005af660` | A `0x0093df20` nullát ad, ezért a másodlagos `0x009d5e90` út fut; ha ez is nulla, a segéd `0`-val tér vissza. Nem nulla másodlagos eredmény `3`-at, különleges érték `0xf4242`-t ad. | Eredeti: `0x005b0494`-`0x005b04b4`, `0x005b0558`-`0x005b0568`, `0x005b0636`-`0x005b06c8` |
| `0x16` → `0x005ae610` | A `0x00a98370` nulla eredménye után a `0x00a983d0` eredménye sem `0xf4242`, sem `-1`; ekkor a képlet nullát állít elő. | Eredeti: `0x005ae610` függvénytest, `0x005ae6f7`-`0x005ae797` |
| `0x1b`, `0x1c` → `0x005af310` | A betűkészlet- és szövegkapukon átjutó ágban a `0x009a9c90` nem nulla eredménye közvetlenül visszatér; a nulla eredménye a további műveletek után `0`-val zár. A betűkészlet-hiány `-1`-et, az érvénytelen/üres szöveg `3`-at ad. | Eredeti: `0x005af35c`-`0x005af3f4`, `0x005af4be`-`0x005af501`, `0x005af651`-`0x005af65b` |
| `0x1f` → `0x005add10` | A `0x00a50c80` nullája a `0x005ade0f` záráson át visszatér; nem nulla eredményét közvetlenül továbbadja. | Eredeti: `0x005add95`-`0x005addaa`, `0x005ade0f`-`0x005ade15` |

**A `0x005b1460` teljes normál visszatérési útja.** A `0x0099d0c0` fájlmegnyitó hívás `rb` módot és `0x2000` paramétert kap. Ha a kapott fájlkezelő nulla, a felszabadító ág után EAX=`-1`. Sikeres megnyitásnál a `0x00c08d3e` olvasás nulla eredménye EAX=`2`-vel tér vissza. Nem nulla olvasás után a `0x00a4c600` értelmezés nullája, illetve az aktuális rekordtípussal (`*esi`) egyező értéke EAX=`-1`-et ad. Új, nem nulla típusnál a kód beírja az `*esi` mezőbe, meghívja a `0x005b1570`-et, eltárolja annak EAX-át a `EDI`-ben, elvégzi a fájl-erőforrás takarítását, majd pontosan ezt az értéket adja vissza. Ezért a `0x005b1460` saját normál útján közvetlenül `0`-val nem tér vissza; nulla csak a sikeres újratípusozás `0x005b1570` eredményéből jöhet. | Eredeti: `0x005b1460`-`0x005b1560` |

**A `0x005b1570` külön és korai ágai.** Ha a `param_2` null értékű mutató (`EDI==0` a `0x005b15fc` ellenőrzésnél), vagy a típusérték `0x04` (`[param_3]==4`), a közös korai kilépés EAX=`2`-t ad (`0x005b1b1c`-`0x005b1b5e`). A `0x00` rekordtípust a `0x00a4c140` előbb átírja. A `0x12` típuság elmenti a `0x005b0730` EAX-át; ha az `3` és a `[this+0xfd]` bájt nulla, elvégzi a `0x009a9c90`/`0x009a91a0` műveleteket, majd a külön záró út EAX=`0`-val tér vissza (`0x005b186a`-`0x005b191a`, `0x005b1b30`-`0x005b1b5e`). Más esetben a segéderedmény a közös útba jut. A közös út a `0xf4242` különleges értékét megőrzi; ha az eredmény nulla, vagy a `0x00a4c0a0` AL eredménye nulla, a `0x005acf40` után a segéderedmény kerül vissza EAX-ba. Nem nulla és elfogadott eredmény esetén a `0x005b1460` EAX-a tér vissza (`0x005b197d`-`0x005b19c1`). A normál vezérlési utak után álló `0x005b19c6` kódrészlet EAX=`1`-et állít; az aktiválási feltételét nem vizsgáltam, és nem tartozik a normál típuságakhoz.

**A `[esp+0x2fa]` jelző és az író keresése.** A jelző olvasási helye `0x004265d1`; a meglévő Ghidra-kimenet (`2026-11-11-6532-colab-decomp-11.txt`, `FUN_00425f60`) ezt a `cStack_1586` helyi változóként azonosítja, és a függvény dekompilált törzsében csak az olvasása szerepel. Az utasítássorban sincs hozzá tartozó közvetlen tárolás. A közeli `0x00426526` cím a helyi adatterület címét átadja a `0x004efa20`-nak. A `0x004efa20` első szavát olvassa, majd a kivett kulcsszöveget átadja a `0x004ed7d0` keresőnek; a megtalált eredményt a második argumentum kimeneti mutatójába írja (`0x004efa6c`-`0x004efa8d`). A helyi adatterület címére nem ír. Így ebben a függvényben és a címátadás vizsgált útjában **nincs azonosított író**. A jelző kezdeti futásidejű értéke/eredete **NINCS MEG**; a bájt az adott kódban írás nélkül olvasódik. A `0x00426383`, `0x004263a8`, `0x004263b2`, `0x004263d4` más veremhelyekre író utasításokat a Ghidra-változótérkép is külön kezeli; ezek nem bizonyítják a `cStack_1586` inicializálását.

**A két független út.**

- **A út:** az index `functions` táblájával határolt függvénytestek helyi utasításszintű olvasása. A diszpécser táblaképzését, a segédek visszatérési utasításait, a `0x005b1460` ágait, a `0x12` zárását és a `0x004265d1` olvasási helyet a binárisban követtem.
- **B út:** a meglévő `2026-10-22-idorend-42.txt` Ghidra kapcsolóág-listája külön felsorolja a típus-segédfüggvény hozzárendeléseket és a `0x12` feltételt; a `2026-11-11-6532-colab-decomp-11.txt` `0x00425f60` változótérképe külön `cStack_1586`-ként azonosítja a jelzőt, csak olvasó használattal. A két út a diszpécser térképén, a `0x12` ág feltételén és a jelző olvasásán egyezik. A Ghidra-kimenet nem mutatja a segédek belső nullás feltételeit, és nem határozza meg a külön ágak EAX-át; ezek ezért feltételesek maradnak.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a `0x004efa20` hívás vagy egy közeli veremírás előállítja a `cStack_1586` jelző értékét. A teljes `0x00425f60` utasításlistában a jelzőhöz nincs közvetlen írás; az egyetlen közeli címátadásnál a `0x004efa20` az első argumentumból csak az első szót olvassa, és a találatot a második argumentumú kimenetbe írja. A `0x004ed7d0` kulcsszöveg-összehasonlító útja a kulcs bájtjait olvassa, a kulcs helyére nem ír. A Ghidra-változótérkép sem rendel írást a `cStack_1586`-hoz. A jelzőre író hívás hipotézise nem állt meg; a kezdeti érték ettől még NINCS MEG.

**PicasaPy-összevetés.** A feltárt numerikus típusok emberi jelentése, vagyis a Picasa- és PicasaPy-rekordokhoz rendelése továbbra is **NINCS MEG**. A `src/picasapy/timeline.py:53` dátumfeloldása, a `TimelineView.qml:133` képsorozat-léptetése és `:277` csúszkája nem feleltethető meg a most feltárt kódnak. A `picasa-idorend-viselkedes.md` sorát ezért nem módosítottam; termékszintű eltérés és fejlesztési teendő ebből a körből nem következik.

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| A `0x005b1570` típus-segédfüggvény hozzárendelései. | bináris (`0x005b17ad`-`0x005b19c1`), Ghidra kapcsolóág-listája `FUN_005b1570` | megerősített |
| A típussegédek fent felsorolt nullás ágai. | bináris (típusonként a táblázatban megadott `0x...` utasításhelyek) | feltételes; egy utasításszintű út |
| A `0x005b1460` normál kilépési EAX-ai: `-1`, `2`, vagy új típusnál a diszpécser EAX-a. | bináris (`0x005b1498`-`0x005b1560`) | feltételes; helyi utasításszintű út |
| A diszpécser paraméter-null és `0x04` korai EAX-a `2`; a `0x12` külön záróág EAX-a `0`. | bináris (`0x005b15fc`-`0x005b1609`, `0x005b1b1c`-`0x005b1b5e`, `0x005b186a`-`0x005b191a`, `0x005b1b30`-`0x005b1b5e`) | feltételes; a végső EAX-t egy helyi utasításszintű út igazolja |
| A `0x00425f60` törzsében a `cStack_1586` olvasódik, közvetlen írása nem látszik. | bináris (`0x004265d1`), Ghidra-változótérkép `FUN_00425f60` | megerősített a függvényen belüli használatra |
| A vizsgált `0x004efa20` címátadási út nem ír a helyi adatterületre; az eredményt a második argumentumú kimenetbe teszi. | bináris (`0x004efa20`, `0x004ed7d0`, `0x004efa6c`-`0x004efa8d`) | feltételes; helyi utasításszintű út |
| A `cStack_1586` kezdeti futásidejű értéke vagy külső eredete. | **NINCS MEG** | nyitott |
| A numerikus típusok emberi jelentése és Időrend-rekordhoz rendelése. | **NINCS MEG** | nyitott |

**A #6532 „Kész, ha” pontjainak állása ebből a körből.** ✅ A célzott segédfüggvények nullás visszatérési útjai és a `0x005b1460` normál kimenete egy utasításszintű úton végigkövetve; a diszpécser `0x12` külön útjának és korai ágainak EAX-a feltételesen dokumentálva. ⛔ A segédfüggvények emberi rekordszerepe nem derült ki; a `cStack_1586` írója/kezdeti értéke NINCS MEG. ⛔ Az egész Időrend-funkció teljes bináris specifikációja és tételes PicasaPy-összevetése továbbra sem teljes. ⛔ Az eredeti Időrend minden kért műveletét lefedő videó/képsor és a kiadási összehasonlító anyag ettől a célzott statikus körtől nem készült el. ✅ A korábban átadott információ szerint a #6713 megvalósítási jegy nyitva van; GitHub-állapotot ebben a körben nem ellenőriztem.

**Nyitott.**

- **NINCS MEG:** a numerikus típusok emberi neve és megfeleltetése a PicasaPy Időrend rekordjaihoz. Ezt a rekordsorok tényleges adatforrásának Ghidra- vagy Colab-videós azonosítása döntheti el; a mostani segédágak önmagukban nem nevezik meg a típust.
- **NINCS MEG:** a `cStack_1586`/`[esp+0x2fa]` futásidejű kezdeti értéke és eredete. A függvényen belüli közvetlen írás és a vizsgált `0x004efa20` címátadási út írása kizárva; további döntő lépés a Colab-futásban a bájt rögzítése a `0x004265d1` olvasás előtt, több friss indítással.
- A segédfüggvény-ágak részletes visszatérési feltételei az utasításolvasási úton feltételesek; az eredeti bináris futásidejű bemenetein nem mértem őket.
#### 38.2.126 Az Időrend sliderthumb és timeline sáv felhasználói művelete és eseményútja (#6532, 2026-11-13)

**Hatókör és döntés.** A `docs/specs/picasa-idorend-viselkedes.md` 38.2.1 táblázatának 2. sorában nyitott kérdés: az `overlays/sliderthumb` fogantyú szemantikai művelete, a csúszka-húzás és a sávkattintás hatása az eredeti Picasa 3.9.141.259 binárisából (SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`). A kérdés lezárva: a `sliderthumb` és a `timeline` sáv nem passzív díszítőelem, hanem közvetlen dátum-kereső (seek slider) vezérlő. A `0x007fde80` egérkezelőben a sávon vagy a fogantyún belüli lenyomás (`WM_LBUTTONDOWN` `0x201`, `+0x429 = 1`) és az egérmozgatás (`WM_MOUSEMOVE` `0x200`) a `0x007fdd00` útján a normalizált x-arányhoz legközelebbi gyűjteményindexet választja ki (`[this+0x514]`, `[this+0x510]`), míg az elengedés (`WM_LBUTTONUP` `0x202`) a `0x007fd770` és `0x007fd0c0` úton elindítja a 3D kártyapálya animációját a kiválasztott fókusz-pozícióra. A sávon kívüli háttérre kattintva és húzva (`+0x428 = 1`) a nézet tehetetlenségi 3D térbeli pásztázást végez (`[this+0x310]` görgetési sebesség, csillapítás 0.95). A fogantyú és a sáv fölött a kurzor lebegtetéskor nem vált mutatót (`0x007fe540`), sima nyíl marad.

**A út - utasításszintű olvasat a binárisból.**
1. *Rétegfelépítés és tárolás (`0x007fa7f0`, `0x007fb210`):* A `QDrawable` objektum (vtábla `0x00cbd66c`) konstruktora `0x007fa7f0` lefoglalja a rétegeket; a `0x007fb210` inicializálja az `overlays/timeline` (`0x00cbd38c`, tároló `[this+0x6c0]`, x kezdőpont `[this+0x6d8]`, szélesség `[this+0x6c8]`, magasság `[this+0x6cc]`) és az `overlays/sliderthumb` (`0x00cbd3b8`, tároló `[this+0x710]`, szélesség `[this+0x718]`, magasság `[this+0x71c]`, futásidejű x pozíció `[this+0x728]`, y pozíció `[this+0x72c]`) adatait.
2. *Rajzolás és kurzor-hit-test (`0x007ffc90`, `0x007fe540`):* A `0x007ffc90` rajzoló a `0x007ffd55` címen kirajzolja a vízszintes sávot (`+0x6c0`), a `0x007ffe21` címen a pontok aránya (`date[i]/date_last`) alapján a `+0x6e8` `overlays/timelinedot` pontokat, és a `0x007ffe87` címen a `+0x710` `overlays/sliderthumb` fogantyút. A kurzor hit-testjét (`0x007fe540`) négyszer hívja meg: kizárólag a négy vezérlőgombra (`+0x530` left, `+0x558` right, `+0x580` exit, `+0x738` startbutton); ha bármelyikre ráfut az egér, a fölé húzási kurzorkép (`+0x5d0`) jelenik meg, egyébként normál `overlays/mouse` (`+0x5a8`). A `timeline` és a `sliderthumb` felett tehát lebegtetéskor nincs kéz alakú kurzor.
3. *Egérkezelő és eseményút (`0x007fde80`):* A virtuális metódus (vtábla `0x00cbd66c` slot 11) a kliensméret arányában skálázott egérkoordinátákkal (`0x420`, `0x424`) dolgozik:
   - `WM_LBUTTONDOWN` (`0x201`, `0x007fe1d9`): ha Időrend módban van (`[this+0x3b8] != 0`), téglalap-határellenőrzést végez a timeline sáv (`[this+0x6c0]`) és sliderthumb (`[this+0x710]`) uniójára. Ha az egér a sáv/fogantyú területén van: beállítja a csúszka-húzás jelzőjét (`*(char *)(this+0x429) = 1`), és közvetlenül meghívja a `0x007fdd00(mouse_x, mouse_y)` függvényt. Ha a sávon kívül kattint (a háttérre vagy kártyákra): beállítja a háttér-pásztázás jelzőjét (`*(char *)(this+0x428) = 1`), és ellenőrzi a kártyákra kattintást (`0x007fd800`).
   - `WM_MOUSEMOVE` (`0x200`, `0x007fdefe`): ha `*(char *)(this+0x429) != 0` (csúszka-húzás aktív), minden egérmozgásra meghívja a `0x007fdd00`-at. Ha `*(char *)(this+0x428) != 0` (háttérhúzás aktív), az x irányú elmozdulást (`dx`) a `[this+0x310]` tehetetlenségi sebességhez adja (`speed = speed * 0.95 + dx * c`).
   - `WM_LBUTTONUP` (`0x202`, `0x007fe1a4`): ha a csúszka-húzás aktív volt (`*(char *)(this+0x429) != 0`), meghívja a `0x007fd770(*(undefined4 *)(this+0x514))` függvényt, amely a kiválasztott indexhez tartozó animációs célsebességet/pozíciót kiszámítja, és a `0x007fd0c0` hívással elindítja a kártyapálya simító animációját. Végül mindkét jelzőt törli (`+0x428 = 0`, `+0x429 = 0`).
4. *A keresőcsúszka algoritmusa (`0x007fdd00`):* Az x bemenetet lekorlátozza a sávra (`[x_start, x_start + width]`), kiszámítja a normalizált arányt (`norm_x = (x - x_start) / width`), és a dátumtömbön (`[this+0x388]`) végighaladva megkeresi azt a gyűjteményindexet (`uVar10`), amelyre az `abs(date[i]/date_last - norm_x)` távolság minimális. Az indexet beírja a `[this+0x514]` mezőbe, a megfelelő `0xf8` bájtos kártyarekord mutatóját a `[this+0x510]`-be (ebből rajzolódik a jobb felső név és év-hónap felirat), és a fogantyú pozícióját `[this+0x728]`-ra frissíti.

**B út - független QEMU-mérés és erőforrás-szerződés.** A 38.2.77 szakaszban rögzített QEMU-i386 futtatási mérés közvetlenül igazolja a `0x007fdd00` működését: ismert x bemenetekre pontosan a legkisebb eltérésű `A[i]/A[n-1]` indexet választja ki, a fogantyú x pozícióját pedig `left + t * width - ((thumb_width >> 1) + 3)` értékre állítja (a tesztállapotban `100 + t * 400 - 15`). A `respack.yt` leltárban szereplő `overlays/timeline` (`245×7`), `overlays/sliderthumb` (`25×23`) és `overlays/timelinedot` (`7×8` és `7×11`) grafikák pontosan ennek a sávos csúszkamodellnek a vizuális elemei. A két független út maradéktalanul egyezik.

**Cáfoló kísérlet (15.2).** Megkíséreltük cáfolni azt az állítást, hogy a fogantyú húzása közben a 3D kártyapálya nem mozdul el, és a kameramozgás csak elengedéskor indul el.
- Ellenőrzés: A `0x007fdd00` teljes utasításkészletében kizárólag a `[this+0x514]` (index), `[this+0x510]` (fókusz-rekord) és `[this+0x728]` (fogantyú x) mezők kapnak új értéket. A kameramozgató `0x007fd0c0` hívás a `0x007fdd00`-ban nem szerepel.
- A `0x007fd0c0` hívója a `0x007fd770`, amely kizárólag a `WM_LBUTTONUP` (`0x202`, `0x007fe1a4`) ágon és a kártyára kattintáskor (`0x007fd800`, `0x007fd8a9`) fut le.
- Eredmény: A cáfolat igazolta az elméletet: a csúszka húzása közben a 3D kártyapálya nem mozog folyamatosan a fogantyúval együtt; csak a fogantyú és a fejléc felirata (a kiválasztott gyűjtemény) frissül azonnal, a kártyák a felengedéskor animálnak a kiválasztott pozícióra.

| Állítás / érték | Forrás |
|---|---|
| A sáv (`overlays/timeline`) és fogantyú (`overlays/sliderthumb`) tárolása | bináris (`0x007fa7f0`, `0x007fb210`, `0x00cbd38c`, `0x00cbd3b8`) |
| Lebegtetéskor nincs kéz alakú kurzor a csúszkán | bináris (`0x007ffc90`, `0x007fe540`) |
| Sáv/fogantyú kattintás felismerése és húzás indítása (`+0x429 = 1`) | bináris (`0x007fde80` @ `0x007fe1d9`) |
| Háttérre kattintás felismerése és tehetetlenségi pásztázás (`+0x428 = 1`) | bináris (`0x007fde80` @ `0x007fe1d9`, `0x007fdefe`) |
| Folyamatos indexkeresés és fókusz-rekord frissítés húzáskor | bináris (`0x007fdd00`, `[this+0x514]`, `[this+0x510]`), QEMU mérés (38.2.77) |
| Felengedéskor kameragörgetési animáció indítása a kiválasztott indexre | bináris (`0x007fde80` @ `0x007fe1a4`, `0x007fd770`, `0x007fd0c0`) |

**PicasaPy-összevetés.**
A PicasaPy `TimelineView.qml`-je (277-290. sorok) az `updateSliderFromX(x)` és `releaseSlider()` függvényekkel pontosan ezt a kétfázisú csúszkamodellt valósítja meg:
- Húzás közben az `updateSliderFromX(x)` a normalizált sáv-arányból kiszámítja a `pendingSliderIndex`-et a `timelineController.sliderIndex()` segítségével.
- A `timeline_motion.py:69-82` `slider_index()` és `85-92` `slider_thumb_x()` függvénye a 38.2.77 specifikáció alapján pontosan a legkisebb távolságú indexet és a sávra korlátozott fogantyúpozíciót adja.
- Elengedéskor a `releaseSlider()` meghívja a `show.animateTo(pendingSliderIndex, 4000)` animációt.
- A háttér húzása a `TimelineView.qml`-ben (`draggingCarousel`, `carouselVelocity *= 0.95`) funkcionálisan megfelel az eredeti `[this+0x310]` tehetetlenségi pásztázásának.
- Eltérés / teendő: A PicasaPy-ban a fejléc gyűjteménynév és dátum felirata húzás közben még nem frissül azonnal a `pendingSliderIndex`-re, csak az animáció lefutása után; az elengedési animáció ideje jelenleg fix 4000 ms, míg az eredeti a kártyatávolságból és az animációs sebességből számítja a lefutást.

**A #6532 „Kész, ha” mérlege.** ✅ Az eredeti felvételek korábbi szakaszokban dokumentáltak. ✅ A sliderthumb és a timeline sáv felhasználói művelete és eseményútja bináris címekkel igazolt és lezárt. ✅ A megvalósítási összevetés elkészült. ⛔ A #6532 további nyitott pontjai (forráshalmaz-szűrők, élő felvételes képkocka-időzítés) még folyamatban vannak.

**Javasolt megvalósítási jegybővítés (#6713-hoz).**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `sliderthumb` húzása közben a `0x007fdd00` minden egérmozgásra frissíti a `[this+0x514]` indexet és a `[this+0x510]` kártyarekordot, így a fejléc felirata (név és év-hónap) húzás közben azonnal követi a kurzort; a felengedéskor a `0x007fd770` indítja a célkártyára animálást. | A `TimelineView.qml:277-290` csak a `pendingSliderIndex`-et frissíti és a fogantyút mozgatja; a fejléc és a fókusz csak a `releaseSlider()` után animál be. | A `TimelineView.qml`-ben a `pendingSliderIndex` változásakor kösd be a fejléc előnézeti feliratának azonnali frissítését húzás közben is. Az elengedési animáció idejét igazítsd a fókusztávolsághoz a fix 4000 ms helyett. |

**Nyitott.** Nincs új nyitott kérdés a sliderthumb és a timeline sáv eseményútjára; a mechanizmus statikusan és mérve lezárva.

#### 38.2.127 A billentyű-, üres belépési, betöltési és visszatérési utak (#6532, 2026-11-13)

**Hatókör.** Ez a célzott zárókör a viselkedési lap öt kiválasztott A pontjából vizsgálja a Ctrl+Space-t, a Space első képét, az üres belépést, a betöltésjelzőt, valamint az Escape/Vissza általános visszatérését. Nem vizsgálja a gombképeket, a fedőréteget, az animációs képkockahatárokat, a kártyaforrás-listát vagy a dátumtömböt. Wine és előkészített PE→QEMU harness nem érhető el; a `qemu-i386` csak Linux i386 ELF-et futtat, a helyi C fordító AArch64 célú. Emiatt új futásidejű képkocka- vagy UI-mérés nem készült.

##### 1. Üres belépés - feltétel és PicasaPy-eltérés

**A út - eredeti bináris.** A `0x005e8a70` közös bemutató-mód kezelő a `0x005d2a70` eredményét vizsgálja. Ha ez 0, vagy ha a `CThumbUI+0x2c0` objektum `+0x154` mezőjének `0xfffffffe` maszkolt értéke 0, a `0x005e8a70` az `IDS_MUST_SELECT` sztringet (`0x009ae710`) kéri le, majd a `0x009807f0` üzenetutat hívja. A `0x005d2a70` a `CThumbUI+0x2bc` szolgáltató elemsorán végighalad, és a nem nulla `state` értékű rekordokat számolja. A gyűjtemények feldolgozása után a függvény az összegyűjtött rekordok kódolt darabszámát (`uStack_d0 & 0xfffffffe`) is vizsgálja; 0 esetén ugyanazt az üzenetet adja. A MakeTimeline hívóút a `0x005da7ab`-`0x005da7ae` helyen vezet a `0x005e8a70` felé.

**B út - független adat- és forrásellenőrzés.** A szöveg-erőforrás xrefje a `0x00e01776` UTF-16 szöveget a `0x005e8a70` függvényhez köti: `You must have images in the Picture Tray to do this.` A `CThumbUI+0x2c0` mező `CAlbumState` típusa a konstruktor/RTTI-útból ismert; a MakeTimeline külön count/index útja a `0x005e9434` címen a `0x004a0980`-nak adja át ugyanezt az objektumot, amely a `[state+0x13c] >> 1` elemszámot adja vissza (38.2.63). Üres CAlbumState-listánál a MakeTimeline feldolgozó ciklusa ezért nulla iterációt végez, az eredménylista üres marad, és a `uStack_d0` utólagos kapuja ugyanazt az üzenetet küldi. A `+0x2bc` ettől külön `CThumbDB` szolgáltató. A PicasaPy forrásában a Ctrl+5 út újratölti és megnyitja az Időrend panelt akkor is, ha a modell üres; a `TimelineView.qml` ilyenkor `currentIndex = -1` értéket állít be, és nincs üresállapot-üzenet (`MainKeyboardShortcuts.qml:406-412`; `MainTimeline.qml:96-104`; `TimelineView.qml:259-265`).

**Következtetés.** Az eredeti nem indít bemutatót, ha nincs állapotképrekord, ha a kódolt CAlbumState-listaszám maszkja nulla, vagy ha a szűrés után üres a qshow bemeneti rekordlistája; mindhárom eset az `IDS_MUST_SELECT` üzenethez vezet. A PicasaPy megnyitja az üres Időrend nézetet. Az `+0x154` mező emberi jelentését nem állítom; a gyűjtemény nélküli esetet a külön, `+0x13c` elemszámot olvasó MakeTimeline út is alátámasztja.

**Cáfoló kísérlet (15.2).** Azt próbáltam cáfolni, hogy az `IDS_MUST_SELECT` lelet az Időrend belépésére vonatkozik, nem csak valamelyik másik közös bemutató-módra. A `0x005da7ab` timeline parancs-hívásától a `0x005e8a70` közös kezelőig követtem az utat, és ellenőriztem, hogy ugyanebben a függvényben szerepel a `Preparing timeline...` út is. Ez a leletet az Időrend-belépőhöz köti. A cáfoló kontrollja az erőforrás-xref: az `IDS_MUST_SELECT` szöveg hivatkozása ugyancsak a `0x005e8a70`-re mutat. A vizsgálat nem nevezi meg emberi nyelven a `+0x154` mezőt; csak a maszkolt bináris feltételt rögzíti.

##### 2. Ctrl+Space és Space első képe

**A út - billentyűágak.** A `0x00801270` `WM_KEYDOWN`/Space-kezelőjében a Ctrl+Space ág a `[this+0x3ba]` jelzőt 1-re írja (`0x008012fb`) és kezelt eredménnyel tér vissza; ebből az ágból nem hívja közvetlenül a `0x00801130` normál Space-váltót vagy a `0x00803110` objektumváltót. A külön normál Space-ág `[this+0x3bb] == 0` esetén a `0x00801130`-at hívja (`0x00801334`), nem nulla esetén a `0x00803110`-et (`0x0080131f`). A `0x00801130` a `+0x3bb` állapotot fordítja át, majd a `+0x3ba` értékétől függően a `0x00aa6f40` segédhívást kihagyhatja. A `0x00803110` az objektum állapotát módosítja és a host aktív objektumát cserélő `0x00802be0`-t hívja.

**B út - kezelőazonosítás és PicasaPy-forrás.** A qshow `QDrawable` vtable-jének `+0x30` slotja a `0x00801270`; a vtable/RTTI-út és a közvetlen billentyűág-olvasat külön vizsgálatból egyezik (38.2.63). A PicasaPy `TimelineView.qml` ugyanazt az ágat futtatja minden Space eseményre, mert a QML az `event.key` mezőt vizsgálja, a `event.modifiers` értékét nem (`TimelineView.qml:393-406`). A Ctrl+Space ezért PicasaPy-ban a `startCurrentSlideshow()` műveletet kéri.

**Következtetés.** A két program billentyűútja eltér. Az eredeti Ctrl+Space elsődlegesen a `[this+0x3ba]` jelzőt írja; a PicasaPy közvetlenül elindítja az aktuális gyűjtemény diavetítését. Az eredeti jelző látható következménye nem ismert, mert a `0x00aa6f40` meglévő dekompilálása csak a `+0x84` virtuális hívást mutatja, a célosztályt/hatást nem. A Ctrl+Space megvalósítási eltérés ezért nem kap fejlesztői javaslatot, amíg a hatás nem tisztázódik.

**Space első fotója.** A normál Space eredeti belépőága ismert, de a qshow fókuszrekordjából átadott első fotó nem. A `0x00803110` meglévő Ghidra-kimenete a qshow belső objektumát és host-váltását mutatja, de nem nevezi meg az első vetített rekordot. A PicasaPy `MainTimeline.qml` az aktuális kollekció diavetítési modelljének 0. sorával indul (`MainTimeline.qml:106-125`). Az eredeti első fotó kérdésére nincs bizonyított válasz.

##### 3. Betöltésjelző

A `0x005e8a70` timeline ága a `Preparing timeline...` szöveget a `0x009ae560` szövegkezelőn át előkészíti, majd a `0x00415500` folyamatjelző segédhez jut (`0x005e9476`). A segéd `ytProgress::vftable` objektumot inicializál, meghívja a `0x00415380` frissítőt, majd ha a folyamatjelző fogadójának mutatója nem nulla, meghívja annak virtuális `+0x14` metódusát a szöveggel. A feldolgozás végén a fogadó virtuális `+0x0c` metódusát hívja. A `string_xrefs.csv` külön xrefje a `Preparing timeline...` szöveget a `0x005e8a70`-hez rendeli.

**Következtetés és határ.** Bizonyított, hogy a timeline belépőút folyamatjelző objektumot és visszahívó fogadót használ. Nem bizonyított, hogy az adott futásban a fogadó mutatója nem nulla-e, melyik konkrét UI-objektum a cél, vagy a callback felhasználó által látható jelzőt rajzol-e. A PicasaPy QML nyitóútja nem jelenít meg folyamatjelzőt (`MainTimeline.qml:96-104`; `TimelineView.qml:319-324`), ezért a látható eltérés még nem dönthető el.

##### 4. Escape és Vissza: általános visszatérési út

Az Escape handler (`0x007fb820`) a oneup gazdaobjektum vtable `+0x14` metódusát hívja; a `0x008032e0` `oneup/exit` ága ettől független eseményútból ugyanezt teszi. A `0x008037e0` a oneup `+0x50` mezőjébe a `0x00982bf0` által létrehozott `ytWindow` qshow hostot teszi; a RTTI a host vtable-ját `0x00cd87fc` címen azonosítja, a `+0x14` slot célja `0x00983270`. A `0x00983270` normál ágában a host saját `[this+0x6c]` HWND-jére `PostMessageA(WM_CLOSE=0x10,0,0)` hívás kerül, ha a `DAT_00d67858` értéke 1-nél kisebb; másik globális állapotnál szálablak-felsoroló ág fut.

**B út - külön Vissza gomb és host callback.** A Vissza/Exit esemény kezelője (`0x008032e0`) Escape-től külön ágon, a oneup `+0x50` host pointerének vtable `+0x14` slotján át jut a `0x00983270`-hez. Ez a host-művelet bezárási üzenetet küld, nem választ a qshow kártyalistájából új fotót. A két hívóág ezért egyezik abban, hogy ugyanazon qshow host visszatérési útját zárja.

**PicasaPy-összevetés.** A QML zárófüggvény (`MainTimeline.qml:89-94`) kifejezetten a fókuszált kollekciót nyitja meg és annak `firstPhotoPath` képét választja ki, majd bezárja a Timeline ablakot. Az eredeti bizonyított művelete a qshow host bezárása; a host mögötti UI pontos gyűjtemény-/fotókijelölését a statikus callback nem nevezi meg. A viselkedési táblázat ezért nyitva hagyja a nem job-239 belépési út utáni pontos kijelölést, miközben a közös Escape/Vissza záróutat dokumentálja.

**Cáfoló kísérlet (15.2).** Azt az ellenhipotézist próbáltam megcáfolni, hogy a Vissza gomb másik, helyi navigációs parancsot hajt végre, mint az Escape. A két eseménykezelő külön ágát önállóan követtem a `ytWindow` vtable `+0x14` slotjáig, majd a cél `0x00983270` törzsét ellenőriztem. Mindkét út a qshow host bezárási/ablak-enumerációs callbackjére jut; egyik hívóban sem szerepel külön fókuszkártya- vagy fotóindex-kiválasztás. A cáfoló eredménye a callback út azonosságát támasztja alá, de nem zárja ki a Windows `WM_CLOSE` utáni külső, futásidejű állapot-helyreállítást.

##### 5. Bizonyíték- és nyitottkérdés-tábla

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| Az üres belépés `IDS_MUST_SELECT` ága: nincs állapotképrekord, nulla kódolt CAlbumState elemszám, vagy üres szűrt qshow-rekordlista. | bináris (`0x005e8a70`, `0x005d2a70`, `0x005e9434`, `0x004a0980`); üzenet-xref (`0x00e01776`); PicasaPy-forrás (`MainKeyboardShortcuts.qml:406-412`, `TimelineView.qml:259-265`, `MainTimeline.qml:96-104`) | feltételes; a kapu utasításútja és a független count/index út egyezik, élő üres katalógus nem lett mérve |
| Ctrl+Space közvetlenül a `[this+0x3ba]` jelzőt írja, nem a normál Space kezelőt hívja. | bináris (`0x00801270` @ `0x008012fb`); QDrawable vtable (`0x00cbd66c` `+0x30` → `0x00801270`); PicasaPy QML (`TimelineView.qml:393-406`) | feltételes a látható következményre; a közvetlen flag-írás bizonyított |
| A normál Space az eredeti lejátszási útba lép, de az első fotó nincs azonosítva. | bináris (`0x00801270`, `0x00801130`, `0x00803110`); PicasaPy (`MainTimeline.qml:106-125`) | nyitott |
| A timeline megnyitása `ytProgress` callbackot készít elő a `Preparing timeline...` üzenettel. | bináris (`0x005e8a70`, `0x009ae560`, `0x00415500`, `0x00415380`); string-xref (`0x005e8a70`) | feltételes a látható rajzolásra; callback-út bizonyított |
| Escape és `oneup/exit` külön útból a qshow `ytWindow` host callbackját hívja. | bináris (`0x007fb820`, `0x008032e0`, `0x008037e0`, `0x00982bf0`, `0x00983270`); RTTI/vtable (`0x00cd87fc`) | megerősített a hívásút egyezésére; a pontos szülőválasztás nyitott |

**Nyitott, pontos megszerzési út.**

- Ghidra-kör kell: 0x00aa6f40 - mi a `[qshow+0x26c]` vtable `+0x84` célművelete, amelynek hívását a Ctrl+Space által beírt `+0x3ba` jelző kihagyja, és van-e ennek felhasználó által látható következménye? A meglévő dekompiláció a virtuális hívás célját és hatását nem nevezi meg. [blokkoló]
- Ghidra-kör kell: 0x00803110 - a qshow Space-átmenetében mely képrekordot és indexet adja át elsőként az aktív OneUp vetítési objektumnak? A meglévő kimenet csak az állapotváltást és a host aktívobjektum-cseréjét mutatja. [blokkoló]
- Ghidra-kör kell: 0x005e8a70 - a timeline ág `0x00415500` hívásának mely konkrét progress-sink objektum a tulajdonosa, és mely vtable-implementáció fogadja/rajzolja a `Preparing timeline...` üzenetet? A meglévő kimenetben a `piStack_6c` target és az `0x00415500` virtuális `+0x14` callback célja nincs feloldva. [blokkoló]
- A nem job-239 belépési út szülőablakának tényleges kijelölése (`collection`, `photo`, `index`) **NINCS MEG**. Megszerzése: az eredeti Picasa futó Colab-mérésében a timeline megnyitása előtt rögzíteni a szülőnézetet és kijelölt fotót; ezután Escape, majd a külön `oneup/exit` Vissza gomb; a két zárás után képernyőképen és ablaklistán rögzíteni a szülőnézetet és a kijelölést.

**A kiválasztott 5 pont állapota.** ✅ Az üres belépés kapujának bináris feltétele és PicasaPy-eltérése dokumentálva. ⛔ Ctrl+Space látható következménye, ⛔ Space első fotója, ⛔ a `ytProgress` tényleges látható rajzolása, ⛔ a nem job-239 visszatérés pontos szülőkijelölése nyitott. A viselkedési lap 14 eredeti A pontjából így **13 marad nyitva**; a #6532 nem zárható le.


#### 38.2.150 A kártyák véletlen szórása és az Időrendből indított diavetítés beállítása (#6532, 2026-11-13)

**Hatókör és módszer.** A #6532 két nyitott pontja: (1) milyen generátor, milyen mag, mely kártyatulajdonság és milyen tartomány áll a kártyák véletlen szórása mögött, és ez egyezik-e a PicasaPy `timeline_motion.py:100-131` és `TimelinePanel.qml:250-260` megoldásával; (2) az Időrendből indított diavetítés melyik beállítást (időköz, átmenet) használja a job-373 felvételen, és a PicasaPy ugyanezt teszi-e. A helyi `Picasa3.exe` (3.9.141.259, SHA-256 `644b7bec...`) utasításait capstone-nal olvastam; a teljes bináris bájtpásztázása és a mezőírók listája a `paszta.memoria_kapu()` mellett, függvényenként futott. A mérések két forrásból jönnek: (a) `qemu-i386` alatt az eredeti gépi kód futtatása (a privát repó `qemu_harness/hb.py` helyi másolatával: a `__getptd` `0x00bf0583` hamis szálankénti adatblokkot ad vissza, az FPU vezérlőszó `0x27f`, a vizsgált szakasz végén, a `0x008016cd`, illetve a `0x0080150d` és `0x0080188b` címeken egy kiíró rutin veszi át a futást); (b) a job-373 felvétel (`picasa-colab-jobs` kiadás, `video__04.mp4`, SHA-256 eleje `be0ba93e5ac9863f`, 1280x1024, 15 kép/mp, 1500 képkocka) képkockáinak közvetlen vizsgálata. A feladat csak egy Space-t küld, Play-t nem (`ctrl+5`, `Right`, `Right`, `space`, 15 s várakozás, `Escape`). A felvételen futó program hash-e továbbra sincs rögzítve. Az ideiglenes fájlok a munkafa `.bt/` mappájában voltak, a kör végén törölve.

**Rövid eredmény.**

1. **Helyesbítés (38.2.102 §3, 38.2.105, a viselkedési lap összevetése): a `0x008014d0` nem a kártyák kötegszórása.** A függvény a rekordépítés előtt kaput tartalmaz: ha a qshow `+0x3bc` és `+0x3bd` jelzője is nulla, a függvény a régi rekordsort felszabadítja, `rand()` hívása nélkül visszatér. A két jelzőt kizárólag a konstruktor nullázza, és a billentyűkezelő állítja 1-re, `Ctrl+F` (`+0x3bc`), illetve `Ctrl+B` (`+0x3bd`) hatására. Alap Időrend-használatban (nyilak, Space, Escape) tehát a `0x008014d0` nem szór semmit. Az `[-0,075; +0,075)` tartomány csak a rejtett módban a sebességvektor egyik összetevője, nem kártyaeltolás.
2. **A generátor: az MSVC CRT `_rand` (`0x00c08221`)**, szálanként külön 32 bites állapottal (`ptd+0x14`), `állapot = állapot * 214013 + 2531011`, kimenet `(állapot >> 16) & 0x7fff`. A kezdőérték szálanként 1 (`0x00bf0471`-`0x00bf0474`), amíg ugyanazon a szálon `_srand` nem fut. A qshow kódjában nincs `_srand`; a tíz `_srand`-hívó közül három időből magoz (`0x0085b730`, `0x00917f50`, `0x00990000`). Hogy a qshow szálán ezek előbb lefutnak-e, nyitott (lásd lent).
3. **A kártyák kötegszerű kinézete létezik az eredetiben** (job-373, 12, 19 és 28 s: a piros kártya egy lap, a kék és a zöld több, egymásra tolt, kissé elforgatott lap), de a kártyarajzoló (`0x007fd180`) rekordonként egyetlen képet rajzol, a `0x007fc7c0` pedig a CThumbDB rekordképét másolja a kártyarekord `+4` képébe. A lapok elhelyezésének forrása ezért a kártyakép előállítója, ami **NYITOTT** (cím lent). A PicasaPy `card_stack_offset` `xorshift` eltolásának `[-0,075; +0,075)` tartományára és a `-7/+5` fokos váltakozó elforgatására nincs bináris vagy mért forrás.
4. **A diavetítés időköze a job-373 felvételen 3 másodperc** (a felvételen olvasható `Display Time 3 seconds` felirat és a bináris alapérték egyezik). **A diavetítés nem indul lejátszással:** az Időrendből az első Space szünetelő állapotú diavetítő felületet hoz be, az 1/7 kép 15,5 másodpercig pixelre azonos marad. A PicasaPy `start(0)` útja `playing = true` értékkel indul, és 3 másodperc múlva lép. **Eltérés.**
5. Az átmenet fajtáját és időtartamát az Időrendből indított diavetítésre a felvétel nem méri (nincs képlépés benne): **NYITOTT**.

##### §1 A generátor és a mag

| Állítás | A út (utasításszint) | B út (adat, hívó vagy mérés) |
|---|---|---|
| `0x00c08221` az MSVC CRT `_rand` | `call 0xbf0583` (`__getptd`), `ecx = [eax+0x14]`, `imul ecx, ecx, 0x343fd`, `add ecx, 0x269ec3`, `[eax+0x14] = ecx`, `(ecx >> 16) & 0x7fff` (`0x00c08221`-`0x00c08242`) | QEMU az eredeti kódon, hamis szálblokkal, négy maggal (1, `0x3039`, `0xdeadbeef`, 0), mindegyikből hat hívás: minden kimenet egyezik a `s = s*214013 + 2531011; (s >> 16) & 0x7fff` képlettel és a végállapottal. Mag 1 kimenete: 41, 18467, 6334, 26500, 19169, 15724. Az index és a nyers `E8`/`E9` bájtpásztázás ugyanazt a 43 hívó függvényt adja (két további hívás a `0x00b6a0e0` és `0x00b6a133` címen az indexelt függvénytáblán kívül esik, nem qshow-tartomány). |
| A szálanként külön állapot `ptd+0x14`, kezdőértéke 1 | `0x00bf0471` `xor edi, edi`, `0x00bf0473` `inc edi`, `0x00bf0474` `mov [esi+0x14], edi` a `__initptd`-ben (`0x00bf044d`) | A CRT-tartomány (`0x00bef000`-`0x00c0b000`) összes `[reg+0x14]` tárolásának bejárásában a szálállapotot csak a `__initptd` (`0x00bf0474`), a `_srand` (`0x00c0821d`, `[ptd+0x14] = arg`) és a `_rand` (`0x00c08235`) írja; a többi találat helyi változó vagy más szerkezet (`strtoxl`, `gmtime`, `qsort`). A `__mtinit` a fő szálra a `0x00bf0887` hívással futtatja a `__initptd`-t. |
| A qshow nem hív `_srand`-ot | A `_srand` (`0x00c08214`) hívói: `0x00423780`, `0x00565920`, `0x00680370`, `0x0071d940`, `0x0071e120`, `0x0085b730`, `0x0087cb70`, `0x0088fcf0`, `0x00917f50`, `0x00990000`; egyik sem esik a `0x007f9000`-`0x00804000` tartományba | A nyers `E8`/`E9` pásztázás ugyanezt a 10 függvényt adja. |
| Három `_srand`-hívó időből magoz | `0x0085b76d` (a `0x0085b730` GUID-képző, sztringjei `%I64x`, `%x%x%x%x-`), `0x009180df` (`0x00917f50`, az online ellenőrzés), `0x009902b8` (`0x00990000`, az összeomlás-kezelő): mindegyik előtt `call 0xc0a421` (`time`) | A másik hét hívó közvetlen környezete nem időt ad át: `0x00565920` és `0x00680370` szöveg-ujjlenyomat, `0x0071d940` `index * 0xee6d00b1`, `0x0087cb70` `[ebx+0x10]`, `0x0088fcf0` argumentum (a `0x00423780` és `0x0071e120` forrása a közvetlen környezetből nem olvasható ki). |

**Mag, kimondva.** A qshow a szál `_holdrand` állapotát folytatja, saját magválasztása nincs. Ha az adott szálon `_srand` nem futott, a sorozat az 1-es magról indul, és ugyanazon a szálon minden `_rand`-hívás előrelépteti. Hogy a qshow szálán futott-e korábban időből magozó függvény, **NYITOTT**: ehhez a qshow szálát létrehozó út (a `0x008037e0` hívói) és a három magozó függvény hívói (`0x0085b7e0`, `0x00918290`, `0x009184e0`, `0x009907c0`) szála kell, futásidejű szálazonosítóval (`GetCurrentThreadId`) mérve.

**Hol lép előre az állapot alap Időrendben.** A qshow-tartományban a `_rand` hívói pontosan négyen vannak: `0x007fe600` (képkockánként, kapuzott), `0x008014d0` (kapuzott), `0x00802230` (két hívás, kapu nélkül; `0x007fb540`, `0x007fda00`, `0x00801130`, `0x00801cf0`, `0x00802630` hívja) és a `0x007f9a40` (a `ytAnimSprite` konstruktora, `0x00cbd2a4`, a főablak értékelő csillagjainak `0x005e81e0` hívójától, nem Időrend). A `0x00802230` kimenete (38.2.62: `0 <= x < 0,15 * W`, `0 <= y < 0,075 * H`) a `0x007fff30` `SimpleSlideshow == 0` ágában kerül transzformációba; az alapértelmezett `SimpleSlideshow = 1` mellett (38.2.100) ez a kimenet nem látszik. A kártyák elhelyezéséhez tehát az alap Időrendben nem járul hozzá.

##### §2 A `0x008014d0` kapuja

| Állítás | A út | B út |
|---|---|---|
| `0x008014d0` kilép, ha `[this+0x3bc] == 0 && [this+0x3bd] == 0` | `0x008014f7` `cmp byte [edi+0x3bc], 0`, `jne 0x80150d`; `0x00801500` `cmp byte [edi+0x3bd], 0`, `je 0x80188b`; a `0x0080188b` pop-ok és `ret` | QEMU, a teljes függvény futtatva `edi = this`, a listában 6 elem (`[this+0x3f0] = 12`, `[this+0x3ec]` kitöltve), jelzők 0: a visszatérési érték 0, a CRT állapot a futás után változatlan (mag 1 maradt 1, mag 777 maradt 777), vagyis nulla `_rand`-hívás. A kapu elágazása a valódi bájtokon: (0,0) a `0x80188b` kilépésre, (1,0), (0,1) és (1,1) a `0x80150d` folytatásra jut. |
| A két jelző kizárólag a konstruktor nullázza és a billentyűkezelő állítja be | A konstruktor `0x007fad21`, `0x007fad27` nullázza; a `0x00801270` `0x008013c5` (`Ctrl+F`, billentyűkód `0x46`) és `0x008013fe` (`Ctrl+B`, `0x42`) 1-et ír; a feltétel: `[0xd67849] != 0` és `GetAsyncKeyState(0x11)` felső bitje (`0x008013a5`-`0x008013bf`, `0x008013de`-`0x008013f8`) | A teljes bináris pásztázása a `+0x3bc`/`+0x3bd` bájtra író utasításokra: a qshow osztályban más író nincs (a többi találat más osztály dword-mezője). A `[0xd67849]` írói: `0x0057641b` (ablakállapot-visszaállítás után 1) és `0x00a52e66`, ahol `[edi+4] == 0x1c` (`WM_ACTIVATEAPP`) esetén `[0xd67849] = wParam` bájtja: alkalmazás-aktív jelző. |
| A `0x007fe7c0` és a `0x007fe600` ugyanazzal a kapuval fut | `0x007fe7cf`, `0x007fe7da` ugyanaz a két bájtos vizsgálat, `je 0x7fee5f` kilépés; a `0x007fe600` csak innen hívódik (`0x007fe7e9`) | Az index hívói: a `0x007fe7c0` egyetlen hívója a `0x007ffc90`; a `0x007fe600` egyetlen hívója a `0x007fe7c0`. |

##### §3 Mit szór a rejtett módban, és milyen tartományban

A `0x008014d0` a `[this+0x3ec]` azonosítólista minden elemére (a fókuszgyűjtemény fotói) négy `_rand`-értéket használ; `u = r / 32768`, `r1`..`r4` az egymás utáni hívások. A mezők a 0xf8 bájtos rekordban vannak, amely a `[this+0x2ec]` sorba másolódik (`0x008017ed` `lea eax, [esp+0x50]`, `0x00803b50`). A rekordcímzés A útja: a `0x007fa5b0` konstruktor a `0x0080157c` `ecx = esp+0x50` címen épül, a `0x00a6aa00` hívás `ret 0x14`-gyel tisztítja a rakott téglalapot és célmutatót (`0x00a6aa27`), így a `0x008015ad`-nál az `esp+0x11c`..`esp+0x128` helyi változók a rekord `+0xcc`..`+0xd8` mezői:

| Rekordmező | Képlet (utasítások) | Tartomány |
|---|---|---|
| `+0xcc` (x helyzet) | `u4 - 0,5` (`_rand` `0x00801644`, tárolás `0x0080167d`) | `[-0,5; 0,5)` |
| `+0xd0` (y helyzet) | `u3 - 0,5` (`_rand` `0x00801633`, tárolás `0x008016a7`) | `[-0,5; 0,5)` |
| `+0xd4` (x sebesség) | `0,15 * (u2 - 0,5)` (`_rand` `0x008015be`, szorzás `0x008016ae`-`0x008016b8`), a szorzó az f64 `0,15000000596046448` (`0x00cf3fd0`) | `[-0,075; 0,075)` |
| `+0xd8` (y sebesség) | `[this+0x3bc] == 0`: `0,15 * (-u1)`; `[this+0x3bc] != 0`: `0,15 * (0,5 - u1)` (`_rand` `0x008015ad`, előjelváltás `0x00801611`, feltételes összeadás `0x00801624`, szorzás `0x008016bf`-`0x008016c6`) | `(-0,15; 0]`, illetve `(-0,075; 0,075]` |

**B út (QEMU, az eredeti `0x008015ad`-`0x008016c6` szakasz, a futás a `0x008016cd` címen kiírásra terelve; a QEMU az `esp`-relatív értékeket méri, a rekordmezőkhöz rendelésük a fenti A út számítása).** Négy mag (1, `0x3039`, `0xdeadbeef`, `0x7a69`) és mindkét `+0x3bc` érték mellett az eredeti kód mezői bitre egyeznek a fenti képletek f32-értékeivel (8 futás, 8 egyezés). Mérés (`+0xcc`, `+0xd0`, `+0xd4`, `+0xd8`):

| `+0x3bc` | mag | `+0xcc` | `+0xd0` | `+0xd4` | `+0xd8` |
|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 0,30871582 | -0,30670166 | 0,009535218 | -0,000187683 |
| 0 | `0x3039` | 0,175201416 | 0,287200928 | 0,012725831 | -0,0347168 |
| 0 | `0xdeadbeef` | 0,10333252 | 0,071655273 | 0,002453613 | -0,083940126 |
| 0 | `0x7a69` | 0,027435303 | 0,179534912 | -0,037197877 | -0,018621827 |
| 1 | 1 | 0,30871582 | -0,30670166 | 0,009535218 | 0,074812323 |
| 1 | `0x3039` | 0,175201416 | 0,287200928 | 0,012725831 | 0,040283203 |
| 1 | `0xdeadbeef` | 0,10333252 | 0,071655273 | 0,002453613 | -0,008940125 |
| 1 | `0x7a69` | 0,027435303 | 0,179534912 | -0,037197877 | 0,056378175 |

A régi olvasat (`dx = (rand - 0,5) * 0,15`, `dy` előjeles korrekcióval, mindkettő `record[+0xd4]` és `record[+0xd8]`, "a köteg kártyáinak szórása") hibás volt két ponton: a `+0xd4`/`+0xd8` sebesség, nem eltolás, és `+0x3bc == 0` mellett az y összetevő `(-0,15; 0]`, egyirányú. A másik két `_rand` a `+0xcc`/`+0xd0` helyzetet adja, amit a régi olvasat kihagyott.

**Képkockánkénti mozgás (csak A út, feltételes).** A `0x007fe600` minden rekordra: `dt` a `0x009a51b0` QPC-másodperce a `[this+0x528]` bélyegtől; `x += dt * vx`, `y += dt * vy` (`0x007fe650`-`0x007fe696`); ha `x` vagy `y` 0 alá esik, 1-et ad hozzá, ha 1 fölé, 1-et von le (`0x007fe69e`-`0x007fe6fc`): az egységnégyzet tóruszán kering. Utána mindkét sebességkomponens kap egy-egy `_rand`-ból: `v += 0,001 * u - 0,0005` (f64 `0x00cf3db0 = 0,001`, `0x00cf4858 = 0,0005`; `0x007fe713`-`0x007fe78d`), azaz `[-0,0005; 0,0005)` véletlen járás képkockánként. A `0x007fe7c0` a helyzet `2π`-szeresének szinuszából/koszinuszából (f64 `0x00cf4350 = 6,2831854820251465`) számolja a lapok méretét és sorrendjét, majd rajzol. Ez a rajzút csak a jelzőkkel fut; a fejlesztői átadásban nem kérek belőle semmit. A mozgásképlet második független útja (QEMU a `0x007fe600`-ra, rögzített `dt`-vel) nincs meg, ezért a bekezdés feltételes.

##### §4 A kártyák kötegszerű kinézete: mérés, forrása nyitott

| Állítás | A út | B út |
|---|---|---|
| A kártyarajzoló rekordonként egy képet rajzol | `0x007fd180` a látható rekordokon (`[obj+0x80]`) végigmenve a rekord `+4` képét kéri a `0x00a6ac90` LOD-választón át, a `0x009e6df0` rajzolóval: lapsor, több kép per rekord nincs (`0x007fd1b8`-`0x007fd35d`) | A `0x007fc7c0` rekordonként egyetlen `0x00a6aa00` másolással tölti a `+4` képet (38.2.92); a kártyarekord konstruktora `0x007fa5b0`. A rekord `+0xcc`-`+0xd8` mezőit a `0x007fd180` nem olvassa (a tagpásztázás `0x007fd180`-ban csak `esp`-relatív helyi változót talál). |
| A felvételen a kártyák egy része több lapból áll | | job-373, 12 s: a piros 2009_majus kártya egy lap, a kék 2014_november és a zöld 2019_marcius több, egymásra tolt, kissé elforgatott lap; 19 s és 28 s: ugyanaz a három kártya másik pályahelyen, a kék és a zöld lapelrendezése a szemrevételezés szerint azonos (képpontos összevetés nem készült). |

Következtetés: a lapok elrendezése a kártyakép része (a rekord `+4` képe), nem a `0x008014d0`-ból jön, és a felvétel szerint a fókuszváltások közt látszólag változatlan. Hogy ez a kép mikor és melyik függvényben áll össze, és kap-e véletlenszámot, **NYITOTT**. A lapok száma és a gyűjtemény fotószáma közti kapcsolat is mérés nélkül maradt (a piros 1/1, a zöld 1/7; a többi gyűjtemény fotószáma a felvételről nem olvasható).

##### §5 Összevetés a PicasaPy-val (1. pont) és megvalósítási javaslat

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Az alap Időrendben a qshow nem szór véletlenül kártyaeltolást; a `0x008014d0` rejtett `Ctrl+F`/`Ctrl+B` módban fut, és helyzet- és sebességvektort ad a fókuszgyűjtemény fotóihoz. A kártyák kötegszerű kinézete a kártyakép része, forrása nyitott. | `card_stack_offset` (`timeline_motion.py:100-131`) a gyűjtemény- és fotóindexből magozott `xorshift` algoritmussal `[-0,075; +0,075)` eltolást ad a kártyaméret arányában; `TimelinePanel.qml:250-260` ezt, `-7` és `+5` fokos váltakozó elforgatással alkalmazza, legfeljebb négy fotóra kártyánként. | **Eltér a forrás szerint: az eltolás-tartomány és az elforgatás bináris eredete megdőlt**; a docstring ("A qshow minden kártyánál két `_rand()` értéket használ") téves. A látható viselkedésből egyezik, hogy a köteg stabil és fókuszváltáskor nem változik (a PicasaPy index-magos, az eredeti felvétel szerint látszólag rögzített). |

**Javaslat (a hívónak, kódot nem módosítottam).** (1) A `timeline_motion.py:100-110` docstringből és a `TimelinePanel.qml:250-260` környéki megjegyzésből töröld a `0x008014d0`-re hivatkozást; a tartomány és az elforgatás "mérésből származó, bináris forrás nélküli" jelölést kapjon. (2) A stabil, indexmagos elrendezést tartsd meg: a felvétel szerint a köteg fókuszváltások közt nem változik, ezért a PRNG-algoritmus különbsége nem felhasználói eltérés. (3) Új szórási kód ne készüljön, amíg a kártyakép előállítója nincs azonosítva; a következő bináris irány lent szerepel. (4) A `Ctrl+F`/`Ctrl+B` rejtett mód felhasználói felületen nem szerepel; megvalósítást nem javaslok.

##### §6 A diavetítés beállítása job-373-ban

| Állítás | A út | B út |
|---|---|---|
| Az időköz 3 másodperc | A qshow konstruktora a `Preferences\SlideshowEffectTime` kulcsot a `[this+0x760]` objektumhoz köti, alapérték 3 (`0x007face5`, `0x007facd3`); a `Display Time` `+`/`-` kezelője `0x00802b40` ugyanezt az objektumot olvassa (`0x00802b4c`) és írja (`0x00802bc5`), 1 és 20 közé szorítva (`0x00802b6d` `fld1`, `0x00802b7e`, f32 `0x00cf4974 = 20,0`) | job-373, 31,0 s (465. képkocka), a diavetítő alsó sávja: `Display Time`, `3 seconds`. A felvétel nem állít be Preferences-értéket (alapállapot). |
| Az Időrendből az első Space szünetelő diavetítő felületet hoz be, automatikus léptetés nélkül | `0x007fda5b` `[this+0x3bb] = 0` az Időrend indításakor; `0x00801310` `+0x3bb == 0` esetén `0x00801332` → `0x00801130`, ami `+0x3bb`-t 1-re billenti (`0x0080113f`) és a felületet hozó `0x00802c20`/`0x00aa6f40` ágat hívja (`0x00801159`, `0x0080116a`); a `0x00802060` automatikus léptető `+0x3bb != 0` esetén azonnal kilép (`0x00802066`-`0x00802078` → `0x00802121`) | job-373: a Space körül (30,8-33,8 s) a sáv beúszik, majd a 800x600-as fotóterület (`240,212`) az 507.-739. képkockán (33,800-49,267 s, 233 képkocka) pixelre azonos, az `1/7` felirattal; az Escape 49,3 s körül jön. A lejátszás gomb a felvételen `▶` alakú (szünetel). A job-240 felvétel 3 és 8 s utáni azonos képe (38.2.82) ugyanezt mutatta. |

**Mit jelent ez.** A job-373 futása az alapértelmezett 3 másodperces `SlideshowEffectTime` értéken volt. Az első Space után az eredeti nem lépteti magától a képet; a lejátszáshoz újabb beavatkozás kell (a második Space a `0x00803110`-re vezet, 38.2.65; a Play gomb hatása nincs mérve).

##### §7 Összevetés a PicasaPy-val (2. pont) és megvalósítási javaslat

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Időköz: `SlideshowEffectTime`, alapérték 3 s, 1-20 s között (`0x007facd3`, `0x00802b6d`, `0x00802b7e`); job-373: 3 s. | `slideshowSeconds`, alapérték 3, tartomány 1-20 (`controller_slideshow_mixin.py:95-125`); az Időrend-Space ugyanazt a beállítást használja (`MainTimeline.qml:106-125` → `SlideshowView.qml:50,201-215`, `SlideshowTiming.qml:11-16`). | **Egyezik** (az alapértéken és a tartományon). PicasaPy-futás nem mért. |
| Indulás: az első Space után szünetelő felület, nincs automatikus léptetés (`0x00801130`, `0x00802060`; job-373: 15,5 s pixelre azonos fotó, `▶` gomb). | `SlideshowView.start(index)` `playing = true` értékkel indul (`SlideshowView.qml:212`), a lépésidőzítő futása `visible && playing` (`SlideshowTiming.qml:16`): 3 s után lép. | **Eltér.** A fejlesztői teendő a lenti javaslat. |
| Átmenet: a qshow `SimpleSlideshow` alapértéke 1 (`0x00800297`-`0x008002be`), pixelkeverés nemlineáris görbével, `p = min(1,5 * t / T, 1)` bemenettel (38.2.100). A felvétel képlépést nem tartalmaz. | `slideshowTransition` alapértéke `dissolve`, `slideshowTransitionMs` alapértéke 700 (felső korlát 500, `controller_slideshow_mixin.py:81-89`), a görbe lineáris. | **Nem dönthető el:** az Időrendből indított, lejátszó diavetítés első átmenete nincs mérve. |

**Javaslat (a hívónak, kódot nem módosítottam).** (1) Az Időrend-Space a PicasaPy-ban az első képen szünetelő állapotban nyissa meg a vetítőt (`playing = false` az Időrendből indított `start(0)` után, a lejátszás gomb `▶` állapotával), és a következő Space/lejátszás indítsa az automatikus léptetést a meglévő `slideshowSeconds` értékkel. Ez csak az Időrendből indított vetítésre vonatkozzon, a szokásos (nem Időrendes) indításhoz ne nyúljon. (2) Az átmenet-időzítés ne változzon, amíg a Play utáni átmenet nincs mérve. (3) Ellenőrzés a javítás után: a `SlideshowView` Időrend-indításánál `playing == false`, és `slideshowTimer.running == false`; a szokásos indításnál `true`.

##### Nyitott kérdések mérlege

Nyitott kérdések: 4 nyílt · 5 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 "csak nyitva"

| Kérdés | Állapot | Mi kell hozzá |
|---|---|---|
| Melyik generátor áll a szórás mögött | **LEZÁRVA** (CRT `_rand`, §1) | |
| Mely tulajdonságot szórja a `0x008014d0`, és milyen tartományban | **LEZÁRVA** (§3; rejtett módban helyzet és sebesség; a régi "kártyaeltolás" olvasat megdőlt) | |
| Szór-e véletlenül az alap Időrend kártyaeltolást a `0x008014d0`-val | **LEZÁRVA** (nem, §2) | |
| Az Időrendből indított diavetítés időköze job-373-ban | **LEZÁRVA** (3 s, §6) | |
| Az Időrendből indított diavetítés indulási állapota | **LEZÁRVA** (szünetel, §6) | |
| Mi a kártyakép kötegszerű lapelrendezésének forrása és szabálya (lapszám, eltolás, elforgatás, véletlenszám-e) | **NYÍLT, következő irány megnevezve** | A CThumbDB rekordkép előállítója: `0x004ae430` → `0x00423300` → `0x00448fb0` → `0x004114e0` (a `0x007fc7c0` `0x007fcca7` és `0x008014d0` `0x008015a8` másolásának forrása), és a rekord `+8`/`+0xc` méretű képét ténylegesen feltöltő út. Mérés: ugyanazon gyűjtemények kártyaképe két külön Időrend-megnyitásban (a job-373 második `Ctrl+5` nem nyitott Időrendet, 38.2.82 szerint sem). |
| Melyik szálon fut a qshow, és futott-e rajta időből magozó `_srand` | **NYÍLT** (a szórás alapesetben nem használja, ezért alacsony prioritás) | A `0x008037e0` hívó lánca és a `0x0085b7e0`, `0x00918290`, `0x009184e0`, `0x009907c0` hívók szála (`GetCurrentThreadId` a Colab-futásban). |
| Az Időrendből indított, lejátszó diavetítés első átmenete (fajta, időtartam, görbe) | **NYÍLT** | Colab-feladat: `ctrl+5`, `space`, majd a lejátszás indítása (második `space`, `0x00803110` útja), 8 s felvétel képkockánkénti méréssel; közben a `[this+0x760]` és a `SimpleSlideshow` Preferences-érték naplózása. |
| A `0x007fe600` mozgásképletének második útja (QEMU rögzített `dt`-vel) | **NYÍLT** (a rejtett mód miatt alacsony prioritás) | A `0x009a51b0` visszatérésének rögzítése a QEMU-harnessben, a `[this+0x528]` bélyeggel. |

##### Amit kizártam

- **"A `0x008014d0` kártyánként két `_rand`-ból számol `[-0,075; +0,075]` eltolást, ez a köteg szórása"** (38.2.102 §3, 38.2.105, a viselkedési lap egyezik-sora): megdőlt. Négy `_rand`-ból két helyzet- és két sebességmező lesz, a függvény kapuzott, és nem a kártyarajzoló fogyasztja a rekordot.
- **"A kártyakép több kártyarekordból vagy a `0x007fd180`-ban rétegzett képből áll"**: a rajzoló rekordonként egy képet rajzol; a lapok a kártyakép tartalmában vannak.
- **"A második `Ctrl+5` a job-373 felvételen újranyitja az Időrendet"**: a 60-100 s tartomány képkockái csak a könyvtárnézetet mutatják; az újranyitás-összevetés ebből a felvételből nem végezhető el.
- **"Az Időrendből indított diavetítés magától léptet 3 másodpercenként"**: cáfolt, 15,5 s pixelre azonos fotóval, és a `0x00802060` kilépésével.

##### Bizonyítottság

**Megerősített:** a generátor képlete (két út, QEMU-méréssel) és a szálanként 1-es kezdőállapot (két út: a `__initptd` olvasata és a CRT-tárolások teljes bejárása), a `0x008014d0` kapuja és a jelzők íróinak teljes listája (két út, mérés is), a rejtett módban szórt mezők képletei (két út, mérés is), az időköz 3 s a job-373 felvételen (két út), a szünetelő indulás (két út). **Feltételes:** a `0x007fe600` mozgásképlete (csak A út), a `[0xd67849]` alkalmazás-aktív értelmezése (a `WM_ACTIVATEAPP` ágból olvasva, futásidejű mérés nélkül), a kártyakép-lapok rögzítettsége (szemmel nézve, képpontos összevetés nélkül). **Független újralevezetés (#140) ebben a körben nem futott;** az indítóra marad. A QEMU-mérés szakaszai a valódi gépi kódon futottak, de a vizsgált szakasz a függvény közepéről indult (a `0x008015ad`-`0x008016c6` rész), a teljes függvény pozitív esetű (jelző = 1, lista nem üres) futtatása a segédhívások miatt nem készült; ezt a kapu elágazásának külön mérése (§2) és a mezőképletek mérése együtt fedi.


#### 38.2.140 Gombképek, rétegsorrend és animációs képkockahatárok (#6532, 2026-11-13)

**Hatókör.** A #6532 Időrend-kutatás három nyitott kérdésének lezárása az eredeti `Picasa3.exe` binárisából és a `runtime/respack.yt` erőforráscsomagból:
1. a gombképek (erőforrások és állapotok: alap, lebegés, lenyomott),
2. a fedőréteg (overlay) rétegei és pontos rajzolási sorrendje,
3. az animációs képkockahatárok (indulási és leállási események).

##### §1 A gombképek erőforrásai és állapotai

**Bináris út és erőforrások.** A qshow bemutató-mód overlay-erőforrásait a `0x007fb210` konstruktor-függvény tölti be a `Picasa3.exe` fájlból a `0x00410fa0` betöltővel a `qshow` (`esi`) objektum mezőibe. A vezérlősávhoz négy gomb tartozik:
- **Balra gomb**: `overlays/left` (ASCII sztring a `0x00cbd334` címen; objektummező: `[this+0x530]`; betöltés: `0x007fb223`; kirajzolás és hit-teszt: `0x007fe540` / `0x007ffe97`; kattintáskor: `0x007fd120`). A `runtime/respack.yt` csomagban 31×31 képpontos RGBA réteg, authorolt tervezési téglalapja: `(243, 405, 274, 436)`.
- **Jobbra gomb**: `overlays/right` (ASCII sztring a `0x00cbd344` címen; objektummező: `[this+0x558]`; betöltés: `0x007fb261`; kirajzolás és hit-teszt: `0x007fe540` / `0x007ffead`; kattintáskor: `0x007fd150`). A `runtime/respack.yt` csomagban 31×31 képpontos RGBA réteg, authorolt tervezési téglalapja: `(366, 405, 397, 436)`.
- **Kilépés (rácsra vissza) gomb**: `overlays/exit` (ASCII sztring a `0x00cbd37c` címen; objektummező: `[this+0x580]`; betöltés: `0x007fb31b`; kirajzolás és hit-teszt: `0x007fe540` / `0x007ffec1`; kattintáskor: `0x007fb820`). A `runtime/respack.yt` csomagban 43×28 képpontos RGBA réteg, authorolt tervezési téglalapja: `(8, 404, 51, 432)`.
- **Indító (diavetítés) gomb**: `overlays/startbutton` (ASCII sztring a `0x00cbd3d0` címen; objektummező: `[this+0x738]`; betöltés: `0x007fb413`; kirajzolás és hit-teszt: `0x007fe540` / `0x007ffed5`; kattintáskor: `0x007fb820`, majd `[this+0x2e8]` vtable `+0x18`). A `runtime/respack.yt` csomagban 43×28 képpontos RGBA réteg, authorolt tervezési téglalapja: `(298, 404, 341, 432)`.

**Állapotok (alap, lebegés, lenyomott):**
- **Nincs külön gomb-állapotkép**: A `respack.yt` bináris rétegjegyzékében az `overlays/` névtérben semmilyen állapotváltozat (`_hover`, `_down`, `_pressed`, `_active`) nem létezik. Mind a négy gomb egyetlen statikus RGBA képpel rendelkezik.
- **Lebegés (hover)**: A gombon magán nincs szín- vagy képi változás. A lebegést az egérmutató váltása jelzi: a `0x007ffc90` rajzoló a `0x007fe540` találati ellenőrzései után (`0x007ffe97`-`0x007ffee5`), ha a kurzor (`[this+0x420]`, `[this+0x424]`) a 4 gomb bármelyikének téglalapján belül van, az egérmutatót átváltja a `[this+0x5d0]` rétegre (`overlays/rollovermouse`, `0x00cbd364`, 15×18 képpont); ha kívül van, a normál `[this+0x5a8]` réteget rajzolja (`overlays/mouse`, `0x00cbd354`, 12×19 képpont).
- **Lenyomott (pressed)**: A gomb lenyomásakor (`WM_LBUTTONDOWN = 0x201` a `0x007fde80`-ban) a `0x007fda80` hit-teszt közvetlenül meghívja az adott gomb parancsfüggvényét. Nem állít be vizuális lenyomási elmozdulást, sötétítést vagy alternatív réteget.

**PicasaPy-összevetés:** A `TimelinePanel.qml:424-570` jelenleg QML `Button` elemeket használ, egyedi `Canvas`-szal rajzolt vektoros ikonokkal (`timelineExitIcon`, `timelineLeftIcon`, `timelinePlayIcon`, `timelineRightIcon`), és mesterséges `down` állapot-színezést (`timelineExitButton.down ? ... : ...`). Az eredeti működésben nincsenek ilyen állapot-színezések, és a gombok a csomagolt képeket használják.

##### §2 A fedőréteg (overlay) rétegei és pontos rajzolási sorrendje

A `0x00800a30` fő képernyőrajzoló és a `0x007ffc90` előtérrajzoló utasításszintű végigkövetése alapján a felület rétegei alulról felfelé (z-sorrendben) a következő sorrendben kerülnek a közös háttérpufferbe:

1. **Alap háttérréteg és ovális shell**: `[this+0x46c]` puffer. Ezt a `0x00802180` inicializálja az aktuális fókuszfotó szürkítésével (`0x00802130`), kontrasztnyújtásával (`0x009db610`), valamint az ablakméretre nyújtott `overlays/overlay` (`0x00cbd3e8`, `[this+0x648]`, 640×480 RGBA kép) ráterítésével (`0x009ab410`). A render-ciklusban a `0x008001c0` rajzolja ki legalsó rétegként. Ez a réteg adja az ovális ablakkeretet és az alsó vezérlősáv sötét hátterét.
2. **Szövegfeliratok és vezetőpontok**: A `0x007fee70` (hívva a `0x007ffca2` címről) rajzolja:
   - A kijelölt gyűjtemény nevét (jobbra zárva, 130 képpont magasan, 1 px fekete árnyékkal, `HelveticaNeue MediumCond`, `0x00a48e10`).
   - A hónap/év feliratot (jobbra zárva, 158 képpont magasan, `ytDateTime::Format2` `%s %d` formátummal, `0x00cd89c4`, `0x00c87dd0`).
   - A dátumskála két végfeliratát (pl. `May 2009` és `November 2026`).
   - A címtől a fókuszkártyához vezető 10 pontból álló pontozott ívet.
3. **Beúsztatási segédrétegek (nem használtak)**: `[this+0x620]` és `[this+0x5f8]` rétegek (`0x009ab690` hívások `0x007ffcc9` és `0x007ffcf7` címeken), a megnyitáskor max. 39%-os átlátszósággal (értékük üres, nem rajzolnak képpontot).
4. **Fotókártyák rétege**: A `0x007fd180` (hívva a `0x007ffd05` címről) rajzolja a köbös racionális Bézier-görbe (`0x007fbab0`) mentén elhelyezett kártyákat. A mélységi sorrendet a `0x007fe7c0` előzetesen megállapítja (`FUN_00604480` rendezés).
5. **Időskála tengelyvonal**: `overlays/timeline` (`0x00cbd38c`, `[this+0x6c0]`, 245×7 px, authorolt: `(197, 461, 442, 468)`), kirajzolva a `0x009ab690` által a `0x007ffd2b` címen.
6. **Időskála dátumpontok**: `overlays/timelinedot` (`0x00cbd3a0`, `[this+0x6e8]`, 7×8 px, authorolt: `(215, 462, 222, 470)`), ciklusban kirajzolva a tengely mentén a `0x009ab690` által a `0x007ffe4a` címen.
7. **Időskála csúszka-fogantyú**: `overlays/sliderthumb` (`0x00cbd3b8`, `[this+0x710]`, 25×23 px, authorolt: `(260, 457, 285, 480)`), kirajzolva a fókuszgyűjtemény pozíciójában a `0x009ab690` által a `0x007ffe90` címen.
8. **Vezérlőgombok**: A négy gomb kirajzolása és hit-tesztje a `0x007fe540` függvénnyel (`0x009ab690` blit):
   - `overlays/left` (`[this+0x530]`, `0x007ffe97`-`0x007ffea0`),
   - `overlays/right` (`[this+0x558]`, `0x007ffead`-`0x007ffeb4`),
   - `overlays/exit` (`[this+0x580]`, `0x007ffec1`-`0x007ffec8`),
   - `overlays/startbutton` (`[this+0x738]`, `0x007ffed5`-`0x007ffedc`).
9. **Egérmutató kurzor**: A legfelső réteg a kurzor (`0x007ffee9`-`0x007ffef7`): `overlays/rollovermouse` (`[this+0x5d0]`, 15×18 px), ha a kurzor a 4 gomb bármelyike felett áll; egyébként `overlays/mouse` (`[this+0x5a8]`, 12×19 px), kirajzolva a `0x009ab690` által.
10. **Képernyőre másolás**: A `0x007fe470` MMX-alapú pixelmásoló (`emms`, `0x009dd4f0`) a kész puffert a képernyőablakra másolja.

**PicasaPy-összevetés:** A `TimelinePanel.qml` rétegei eltérnek: a vezérlősáv külön téglalapként (`timelineControlBar`, 400-422. sor) rajzolódik ki, a csúszkatengely és a gombok Canvas/Rectangle elemekből épülnek, és hiányzik a natív kurzorréteg.

##### §3 Animációs képkockahatárok és események

A qshow animációinak indulási és leállási határait az alábbi események és függvények vezérlik:

1. **Belépési (nyitó) animáció**:
   - *Indulási esemény*: Időrend megnyitása (`0x005e8a70` -> `0x008037e0` -> `0x007fda00`). A `0x007fda00` rögzíti a kezdő QPC időbélyeget a `[this+0x430]` mezőbe (`0x007fda3d`), és beállítja a `[this+0x3b8]=1`, `[this+0x3b9]=1`, `[this+0x3be]=1` jelzőket.
   - *Képkocka-lefutás*: A `0x00800a30` minden képkockán a `0x009a51b0` függvénnyel számítja az eltelt másodperceket a `[this+0x430]` bázisból; az értéket a `[0.0, 1.0]` tartományba szorítja (`0x00c79c88` = 1.0f), megszorozza `256.0`-val (`0x00cf39d8`), és ezt a `p` skálát adja át a `0x007ffc90`-nek.
   - *Leállási határ*: Pontosan 1,0 másodperc elteltével (`t >= 1.0s`) a `p` eléri a 256 felső korlátot. A feliratok és skálaelemek beállnak a 100%-os végértékre. További elmozdulás vagy áttűnés nincs.

2. **Gyűjteményváltó / lapozási animáció (kártyamozgás)**:
   - *Indulási események*:
     - Bal nyíl billentyű (`VK_LEFT = 0x25`) vagy egérgörgő fel (`0x008011b0`),
     - Jobb nyíl billentyű (`VK_RIGHT = 0x27`) vagy egérgörgő le (`0x00801210`),
     - Balra overlay gombkattintás (`0x007fda80` -> `0x007fd120`),
     - Jobbra overlay gombkattintás (`0x007fda80` -> `0x007fd150`),
     - Időskála csúszka felengedése húzás után (`WM_LBUTTONUP = 0x202` a `0x007fde80`-ban -> `0x007fd770`).
   - *Kezdőpont*: A fenti hívók mind a `0x007fd0c0` függvényt hívják a `+2.0f` vagy `-2.0f` (`0x00cf3a48`) irányparaméterrel. A `0x007fd0c0` a `0x009a5210` segítségével rögzíti a kezdő QPC-másodpercet, hozzáadja a 2,0 másodpercet végidőként, és a `0x009e6010` segéddel új animátorrekordot ütemez a `[this+0x2f8+0x38]` tárolóba.
   - *Képkocka-lefutás és csillapítás*: A `QDrawable` tick metódusa (`vtable +0x60`, `0x00803ab0` -> `0x00802060`) minden képkockán meghívja a `0x00801cb0`-at, amely a `0x007fc010`-et futtatja. A `0x007fc010` kiértékeli az animátort a `0x009e5f90` függvénnyel, és a sebességet minden lépésben megszorozza a `0x00cf40b0` címen levő `0.95` lebegőpontos konstanssal (`v = v * 0.95`).
   - *Leállási határ*: Az ütemezett rekord futása 2,0 másodperc után lejár (`0x009e5e70`). A látható mozgás az exponenciális 0.95-ös csillapítás miatt már kb. 1,40-1,47 másodpercnél a képponthatár alá csillapodik (ezzel magyarázható a job-373 felvételen mért 1.400 és 1.467 mp-es mozgásablak). Amikor a mozgás lecseng, a `0x007fd8c0` kiválasztja a `0.666`-hoz (`0x00cf4860`) legközelebb eső kártyát (`[this+0x510]`), és ha gyűjteményhatár lépett át, a `0x008018a0` újraépíti a kártyakészletet.

3. **Diavetítés automatikus léptetési animációja**:
   - *Indulási esemény*: Szóköz billentyű (`0x00801270` -> `0x00801130`) vagy az indító overlay gomb (`0x007fda80` startbutton ág).
   - *Kezdőpont és időzítés*: A `0x00802060` rögzíti a QPC időbélyeget a `[this+0x520]` mezőbe. A `0x009a51b0` méri az eltelt időt.
   - *Képkockahatárok és léptetés*: Amikor az eltelt idő eléri a beállított diaidőt (`SlideshowEffectTime` = 3 mp, `0x007facd3`, vagy 4,0 mp az igazolt profilban):
     - A `0x00802630` lapoz a következő diára és elindítja a képkocka-átmenetet.
     - Újra beolvassa a QPC-t (`QueryPerformanceCounter`) a `[this+0x520]` mezőbe, újraindítva a következő dia várakozási ciklusát.
   - *Leállítási esemény*: Escape billentyű (`0x00801270` -> `0x007fb820`) vagy újabb Szóköz leállítja a diavetítést és visszatér Időrend-módba.

##### §4 Bizonyítottság, utak és cáfoló kísérletek

**Bizonyítottsági fok: megerősített.**
- A gombképek, azok overlay mezői és az állapotok hiánya két független úton megerősített (bináris kódút + respack rétegfa).
- A 10 rétegből álló fedőréteg-sorrend megerősített (bináris utasításolvasat + Ghidra dekompilátumok).
- Az animációk kezdő- és végpontjai, a QPC bázisidők, az 1.0 mp-es clamp, a 2.0 mp-es rekordidő és a 0.95-ös csillapítási szorzó megerősített (bináris diszasszembly + konstans-kiolvasás + korábbi QEMU/videómérések).

| Állítás | Forrás | Bizonyítottság |
|---|---|---|
| A négy vezérlőgomb erőforrása: `overlays/left`, `overlays/right`, `overlays/exit`, `overlays/startbutton` | bináris (`0x007fb210`, `0x00cbd334`, `0x00cbd344`, `0x00cbd37c`, `0x00cbd3d0`) | megerősített |
| A gomboknak nincs külön hover/pressed képe a csomagban; a lebegést a kurzor váltása jelzi (`overlays/mouse` vs `overlays/rollovermouse`) | bináris (`0x007fe540`, `0x007ffe97`-`0x007ffef7`, `0x00cbd354`, `0x00cbd364`) + `respack.yt` | megerősített |
| A lenyomás (`WM_LBUTTONDOWN`) nem vált képet, azonnal a műveletet hívja | bináris (`0x007fde80`, `0x007fda80`) | megerősített |
| A fedőréteg rajzolási sorrendje: háttér shell -> feliratok/ívek -> kártyák -> időskála tengely -> pontok -> csúszka -> 4 gomb -> kurzor -> blit | bináris (`0x00800a30`, `0x008001c0`, `0x007ffc90`, `0x007fe470`) | megerősített |
| Belépési animáció: 1,0 mp-es felső korlát (`0.0 .. 1.0 * 256.0`), QPC bázis `[this+0x430]` | bináris (`0x007fda00`, `0x00800a30`, `0x00c79c88=1.0f`, `0x00cf39d8=256.0`) | megerősített |
| Lapozási animáció: 2,0 mp-es rekordidő (`0x00cf3a48=2.0f`), lépésenkénti 0.95-ös sebességcsillapítás | bináris (`0x007fd0c0`, `0x007fc010`, `0x00cf40b0=0.95`) | megerősített |
| Megállási fókusz: a 0.666-hoz legközelebbi kártya kiválasztása | bináris (`0x007fd8c0`, `0x00cf4860=0.666`) | megerősített |
| Diavetítési léptetés: `[this+0x520]` QPC időzítő, automatikus léptetés `0x00802630` | bináris (`0x00802060`, `0x009a51b0`) | megerősített |

**A két független út:**
- **A út (bináris utasításolvasat):** A `Picasa3.exe` gépi kódjának diszasszemblye capstone-nal (`0x007fb210`, `0x007fe540`, `0x007ffc90`, `0x007fde80`, `0x007fda80`, `0x007fd0c0`, `0x007fc010`, `0x00802060`) és a PE adatszekciójából kiolvasott pontos lebegőpontos konstansok (`0x00c79c88` = 1.0, `0x00cf39d8` = 256.0, `0x00cf3a48` = 2.0, `0x00cf40b0` = 0.95, `0x00cf4860` = 0.666).
- **B út (független erőforrás- és dekompiláció-vizsgálat):** A `respack.yt` fájl rétegindexének és fejléceinek közvetlen dekódolása (`tools/picasa/respack.py`), amely bizonyítja az `overlays/` rétegek pontos méreteit és a külön állapotképek teljes hiányát; valamint a Ghidra-dekompilátumok (`2026-10-21-koteg-1021c.txt`, `2026-10-21-idorend-12.txt`, `2026-10-20-idorend-5.txt`, `2026-11-05-idorend-6532-retegek.txt`) és a korábbi Colab videómérések (job-373, job-446). A két út maradéktalanul egyezik.

**Cáfoló kísérletek:**
1. *Gombállapotok cáfolata:* Megpróbáltam cáfolni azt az állítást, hogy a gomboknak nincs külön lenyomott vagy lebegő állapotképe. A `0x007fe540` és a `0x007fda80` részletes kódjában nincs gombonkénti állapotváltó kép vagy elmozdulás; a `respack.yt` rétegjegyzéke kizárja az ilyen nevű rétegek létezését. Az egyetlen interaktív vizuális visszajelzés a kurzor átváltása `overlays/rollovermouse`-ra (`0x007ffee9`).
2. *Rétegsorrend cáfolata:* Megpróbáltam cáfolni a rétegek egymásra rajzolását, feltételezve, hogy a vezérlősáv különálló UI elemként nem része a fő rajzolóhuroknak. A `0x00800a30` és `0x007ffc90` kódja ezt cáfolta: minden elem egyetlen szoftveres pufferbe rajzolódik szigorú sorrendben (háttér -> szöveg/pontok -> kártyák -> skála -> gombok -> kurzor), és a végén a `0x007fe470` egyszerre blitteli a képernyőre.
3. *Animációs időtartam cáfolata:* Megpróbáltam cáfolni a lapozás 2,0 mp-es rekordidejét az 1,4 másodperces videómérés alapján. A bináris utasításai cáfolták az 1,4 másodperces beégetett értéket: a bejegyzett időtartam 2,0 mp (`0x00cf3a48`), de a `0x007fc010` minden híváskor `0.95`-tel csökkenti a sebességet (`0x00cf40b0`), így a látható mozgás exponenciálisan lecseng már 1,4 mp körül.

##### §5 Összevetés a PicasaPy-jal és teendők

| Eredeti (bináris és respack) | PicasaPy (QML) | Teendő |
|---|---|---|
| A négy gomb egyetlen statikus kép (`overlays/left`, `overlays/right`, `overlays/exit`, `overlays/startbutton`). Nincs hover/pressed kép. | `TimelinePanel.qml:424-570`: QML `Button` elemek, Canvas rajzolta ikonok, és `timelineExitButton.down ? ... : ...` stílusú pressed háttérszín-váltás. | Cseréld le a Canvas ikonokat és a szintetikus gombháttereket a natív `overlays/*` képekre. Szüntesd meg a lenyomott/lebegő gombszínezést. |
| A lebegést az egérmutató váltása jelzi: `overlays/mouse` (12×19) -> `overlays/rollovermouse` (15×18), ha a 4 gomb bármelyike felett áll. | Nincs egyedi kurzorváltás az overlay gombok felett (alapértelmezett rendszerkurzor látható). | A gombok fölé érve válts az `overlays/rollovermouse` kurzorképre (vagy `Qt.PointingHandCursor`-ra). |
| A vezérlősáv sötét háttere a háttérképbe ágyazott `overlays/overlay` keret része, nem külön sáv. | `TimelinePanel.qml:400-422`: Külön `Rectangle` (`timelineControlBar`) mesterséges színátmenettel (`GradientStop`). | A vezérlősáv téglalapja helyett az `overlays/overlay` keretet használd, a gombokat és a skálát e fölé rétegezd. |
| Rétegsorrend: Háttér (`+0x46c`) -> Feliratok és vezetőpontok (`0x007fee70`) -> Fotókártyák (`0x007fd180`) -> Skálatengely (`+0x6c0`) -> Pontok (`+0x6e8`) -> Csúszka (`+0x710`) -> 4 Gomb (`+0x530..+0x738`) -> Kurzor (`+0x5a8/+0x5d0`). | `TimelinePanel.qml`: A rétegek sorrendje részben eltér; a csúszka és a gombok nincsenek szigorúan a kártyák és a skála fölé zárolva. | Biztosítsd a fenti 9 lépéses szigorú Z-sorrendet a QML elemek egymásutániságával. |
| Nyitó animáció: pontosan 1,0 másodperces progressz-korlát (`0x00c79c88`), a feliratok és skála 0..100%-ra, a segédrétegek 0..39%-ra futnak be. | `TimelineView.qml`: nincs nyitó progressz-skála, a panel azonnal láthatóvá válik. | Vezess be egy 1,0 másodperces nyitó progressz átmenetet a feliratok és a skála beúszásához. |
| Lapozási mozgás: 2,0 mp-es rekordidő (`0x00cf3a48`), képkockánként 0.95-ös sebességcsillapítás (`0x00cf40b0`), a megállási fókusz a 0.666-os Bézier-pont (`0x00cf4860`). | `TimelineView.qml:45,82-100`: `backgroundFadeDurationMs: 1400`, tetszőleges sebesség és időzítő. | Alkalmazd a bináris 2,0 mp-es bázisidejét és a 0.95-ös csillapítási képletét a kártyamozgatásra, és a 0.666 fókuszválasztást a gyűjteményváltáshoz. |

**A #6532 „Kész, ha” pontjainak állása ebből a vizsgálatból:**
- ✅ **A gombképek és állapotaik**: bináris címekkel és erőforrás-azonosítókkal igazolva (megerősített).
- ✅ **A fedőréteg rétegei és rajzolási sorrendje**: a teljes 10 lépéses rajzolási sorrend bináris címekkel igazolva (megerősített).
- ✅ **Az animációs képkockahatárok**: a nyitó animáció (1,0 mp), a lapozási animáció (2,0 mp, 0.95 csillapítás) és az automatikus diavetítés eseményei és határai bináris címekkel és konstansokkal igazolva (megerősített).
- ⛔ A teljes jegy lezárásához a videofelvétel integrációja és a párhuzamos billentyű-ág lezárása szükséges.

#### §38.2.160 Zárókör: Ctrl+Space, első dia, betöltésjelző és visszatérés (#6532, 2026-11-13)

**Hatókör.** A §38.2.127 négy nyitott pontját vizsgálja: a Ctrl+Space `[this+0x3ba]` jelzőjének olvasóit és képi hatását; a Space vetítés első elemét; a `ytProgress` fogadó látható UI-útját; valamint a nem job-239 út utáni szülőnézet-kijelölést. A kártyaképek belső forrása és a `0x007fe600` nincs vizsgálva. Új videó nem készült. A korábbi job-240 és job-241 megfigyelés csak a már dokumentált mérésekből vehető át: a mostani `meroadat.tar` nem tartalmazza e feladatok nyers képkockáit, ezért itt nem állítok friss újramérést.

##### 1. Ctrl+Space: a jelző rajzolási hatása

**Bináris út.** A teljes `.text` pásztázása a `paszta.py`-val, első műveletként `paszta.memoria_kapu()` hívással, majd az összes x86 általános regiszterbázissal végezve a qshow `[this+0x3ba]` mezőjének íróit és olvasóit azonosította. A `0x007fad15` konstruktorútból írja, a `0x007fda54` visszaállítja; a Ctrl+Space kezelő `0x00801270` a `0x008012fb` címen 1-et ír. A `0x00800a30` rajzoló a `0x00800b60` és `0x00800be5` olvasóknál a jelzőtől függő ágat vesz. Aktív állapotban a `0x00aa6f40` után a `[this+0x3c4]` képobjektumot a `0x008001c0` rajzolónak adja át a teljes qshow rajzterületre; a rajzoló `+0x474/+0x478` méretmezőket használ. A `0x00801f50` frissítési út szintén ellenőrzi a jelzőt és a `+0x3c4` képet. A `0x00801130` a jelző aktív állapotában kihagy egy segédhívást (`0x0080115e`). A `0x006d911c` találat más osztályhoz, `CPVRenderer`-hez tartozik, nem qshow-mező.

**Független kezelőazonosítás.** A qshow `QDrawable` vtable `+0x30` eseményhelye a `0x00801270` billentyűkezelőre mutat, a `+0x40` rajzolóhely pedig a `0x00800a30`-ra (`0x00cbd66c`). Ez külön út a közvetlen billentyű- és rajzolóutasítások olvasatától.

**PicasaPy-összevetés.** A `TimelineView.qml:393-406` csak az esemény `key` értékét vizsgálja, a módosítókat nem, ezért Ctrl+Space-re a Space-hez hasonlóan a `startCurrentSlideshow()` fut. Ez eltér az eredeti külön, a `+0x3c4` képet a rajzterületre tevő ágtól.

**Következtetés.** A látható művelet binárisból megvan: külön képi objektum kerül a teljes qshow rajzterületre, nem a normál Space vetítés indul. A `+0x3c4` képobjektum tényleges forrása és képtartalma **NINCS MEG**; ezért nem állítom, hogy melyik fotót vagy képet látja a felhasználó.

##### 2. Space: az első vetített elem

**Bináris út.** A `0x00801270` Space-ág a `[this+0x3bb]` állapotától függően a `0x00801130` váltóhoz vagy a `0x00803110` OneUp/host objektumváltóhoz jut. A `0x00803110` meglévő Ghidra-kimenete mutatja az aktív OneUp objektum és a host cseréjét, de nem ad át explicit fotóindexet vagy rekordazonosítót; az első fotó rekordja ebből önmagában nem állapítható meg.

**Mérés és PicasaPy-összevetés.** A korábbi job-240 felvétel dokumentált képkockáján a `2019_marcius` gyűjtemény `1/7` képe látszott, `2019-03-08 09:15` dátumfelirattal (§38.2.82). Ez a gyűjtemény első eleme. A PicasaPy a fókuszált gyűjtemény modelljét adja át, és a 0. indexről indítja a vetítést (`MainTimeline.qml:106-125`). Az első elem szintjén tehát egyezik a két út. A konkrét fájlnév PicasaPy-beli azonosítása és az eredeti OneUp objektum által kapott rekordcím bináris visszakövetése **NINCS MEG**.

##### 3. Betöltésjelző: `ytProgress` fogadó

**Bináris hívási út.** A `0x005e8a70` Időrend-belépő `0x005e9476` útja a `Preparing timeline...` szöveget készíti elő, majd a `CThumbUI+0x278` fogadót adja a `0x00415500` konstruktor-segédnek. A `ytProgress` `0x00415500`-ban inicializálódik, frissítője a `0x00415380`; a folyamatjelző objektum a fogadó `+0x14` metódusát hívja a szöveggel, majd a feldolgozás végén a `+0x0c` metódust.

**A fogadó két független azonosítása.** A CThumbUI konstruktor (`0x005643e0`) a beágyazott `+0x278` fogadóra állítja a CThumbUI vtable-t (`0x00c90694`). Az RTTI/vtable módsor a `+0x14` slotot a `0x00566630`-hoz, a `+0x0c` slotot a `0x00566320`-hoz rendeli; ez egybevág a `ytProgress` virtuális hívásaival. A `0x00566630` a `modalprogress/escmessage` szövegobjektumán a `Press ESC key on keyboard to abort` szöveget állít be (az Időrend-hívás 1 argumentummal jut ide; más esetben `Please wait`). A `0x00566320` a `DAT_00d67914 != 0` feltétel mellett a `thumbui/modalprogressfloater` és `thumbui/progressbarfill` elemeket kéri le, azok `+0x68` virtuális metódusait hívja, majd a folyamatjelző állapotát frissíti.

**PicasaPy-összevetés és határ.** A PicasaPy Timeline megnyitó QML útja (`MainTimeline.qml:96-104`, `TimelineView.qml:319-324`) nem tartalmaz folyamatjelzőt. Az eredeti binárisban azonosított felületi cél a modális lebegő ablak, a folyamatjelző sáv és az ESC-üzenet, de a rajzoló kódot a `DAT_00d67914` kapu feltételesíti; annak Időrend-futás alatti értéke és egy ténylegesen látható képkocka **NINCS MEG**. Így az eltérés lehetséges, nem bizonyított futásidejű eltérés.

##### 4. Nem job-239 visszatérés: szülőnézet és kijelölés

**Bináris út.** A `0x007fb820` Escape útja a qshow `ytWindow` gazdaablakának `0x00983270` callbackjáig jut; a normál állapotban az saját HWND-re `WM_CLOSE` üzenetet küld. Ez a statikus út ablakbezárást igazol, de nem nevezi meg a bezárás után kijelölt mappát vagy képet.

**Mérés és PicasaPy-összevetés.** A korábban dokumentált job-241-ben a közvetlen qshow-belépés után három Right következett; Escape után a `2021_eltero_fajlido` mappa és annak első képe, `2021_eltero_fajlido_01.jpg` volt kijelölve (§38.2.83). A PicasaPy záróútja a fókuszált gyűjteményt és annak első fotóját nyitja meg (`MainTimeline.qml:77-94`), tehát e mért út eredménye egyezik. A job-239 belépés előtti `PicasaTeszt` mappájába tért vissza (§38.2.81); a különböző belépési állapotok eredménye nem ad általános visszaállítási szabályt. A job-241 állítás itt a korábbi dokumentált videómérésen alapul; a nyers felvétel a jelenlegi mérőadat-archívumból hiányzik.

##### 5. Bizonyítékok, független utak és cáfoló kísérlet

| Érték / állítás | Forrás | Fok |
|---|---|---|
| A Ctrl+Space a `+0x3ba` jelzőt 1-re írja; a qshow rajzolója a jelző aktív állapotában a `+0x3c4` képet a teljes rajzterületre adja. | bináris (`0x00801270`, `0x008012fb`, `0x00800a30`, `0x00800b60`, `0x00800be5`, `0x008001c0`) | megerősített a vezérlő-/rajzolóút tekintetében; képforrás NINCS MEG |
| A Space út első látható eleme a mért `2019_marcius` csoport `1/7` képe, dátuma `2019-03-08 09:15`. | mérés (korábban dokumentált job-240, §38.2.82; a nyers képkocka ebben a munkamenetben nem volt elérhető) | feltételes |
| A PicasaPy a fókuszált gyűjtemény 0. elemével indít. | PicasaPy-forrás (`MainTimeline.qml:106-125`) | megerősített forrásolvasat |
| Az Időrend `ytProgress` fogadó `+0x14` célja az ESC-üzenetet állítja, a `+0x0c` célja a modális lebegő ablak és folyamatjelző sáv erőforrásait kezeli a `DAT_00d67914` kapu mellett. | bináris (`0x005e8a70`, `0x00415500`, `0x00415380`, `0x005643e0`, `0x00566630`, `0x00566320`, `0x00c90694`) | feltételes a futásidejű láthatóságra |
| A job-241 Escape után a `2021_eltero_fajlido` mappa és első képe maradt kijelölve. | mérés (korábban dokumentált job-241, §38.2.83; a nyers felvétel ebben a munkamenetben nem volt elérhető) | feltételes |
| A PicasaPy a fókuszált gyűjteményt és annak első képét nyitja meg visszatéréskor. | PicasaPy-forrás (`MainTimeline.qml:77-94`) | megerősített forrásolvasat |

**A két független út.**

- **Ctrl+Space:** A út a teljes mezőhivatkozás-pásztázás és a `0x00801270`/`0x00800a30` diszasszembly; B út a `QDrawable` vtable `+0x30`/`+0x40` slotja, amely a billentyűkezelőt és a képkockarajzolót külön azonosítja. Egyeznek: a Ctrl+Space által állított jelzőt a qshow kirajzoló olvassa, és rajzolóágat vezérel. A kép forrását egyik út sem azonosítja.
- **Space:** A út a billentyűkezelő és a `0x00803110` meglévő Ghidra-kimenete; ez az objektumcserét azonosítja, de a fotóindexet nem. B út a job-240 dokumentált videóképkockája (`1/7`, `2019-03-08 09:15`), amely a fókuszgyűjtemény első képét mutatja. A mérés választ ad az adott feladatra, de a két út nem igazolja egymást az átadott rekord kérdésében; ezért az eredeti rekordazonosítás **feltételes/nyitott**. A PicasaPy 0. indexe ugyanilyen sorszintű kezdést valósít meg.
- **Betöltésjelző:** A út a `ytProgress` virtuális hívási lánca; B út a CThumbUI konstruktor, vtable/RTTI és a célfüggvényekben használt erőforrás-nevek. Egyeznek a fogadó, az ESC-üzenet, a modális lebegő ablak és a folyamatjelző sáv azonosításában. A tényleges látható képkockát a globális kapu miatt egyik út sem igazolja.
- **Visszatérés:** A út a `0x007fb820` statikus bezáró callbackja; B út a job-241 felvétel dokumentált kijelölése. A bináris út nem dönti el a szülő kijelölést; a mért út a PicasaPy záróforrásával egyezik, de ez nem független bináris bizonyíték a Picasa eredményére, és csak a job-241 belépési állapotra érvényes.

**Cáfoló kísérlet (módszertan 15.2).** Először azt próbáltam cáfolni, hogy a `+0x3ba` csak nem látható belső jelző. A teljes `.text` pásztázást újrafuttattam `eax/ebx/ecx/edx/esi/edi/ebp/esp` bázisokkal, mert az első keresőminta kihagyta az EBP-t; az így kapott összes qshow-olvasó között ott van a `0x00800a30` rajzolási feltétele, és az út a `0x008001c0` képkirajzolóig ér. A külön vtable-slot ellenőrzés a `0x00800a30`-at render-metódusként igazolja, tehát a cáfoló eredménye ugyanazzal a kétutas mércével ellenőrzött. Másodszor azt próbáltam cáfolni, hogy a progress callback csak könyvelést végez: a `+0x14` cél ESC-feliratot, a `+0x0c` cél UI-erőforrásokat kezel. Ez cáfolja a „csak számláló” feltevést, de a kapu miatt nem bizonyítja a képernyőn ténylegesen megjelent képkockát.

**A §38.2.127 szerinti 14 A pont állása.** A korábbi 13 nyitott A pontból e körben csak a Ctrl+Space rajzolóágat zárja le két független, egyező bináris út. A job-240 első diáját mérő felvétel és a job-241 visszatérés mért eredményt ad, de az adott eredményhez nincs második, független eredeti-Picasa út; ezek feltételesek. A `ytProgress` futásidejű láthatósága is nyitott. Így **12 A pont marad nyitva a 14-ből**; ez a teljes #6532-t nem zárja le.

##### 6. Nyitott

- A `[this+0x3c4]` képobjektum forrása/tartalma: **NINCS MEG**; további lépésként a `0x007fa855` konstruktor és a `0x007fee06`/`0x00800a30` használati út adatbetöltőjét kell követni, kártyakép- és `0x007fe600` vizsgálat nélkül.
- A Space által ténylegesen az OneUp objektumnak átadott fotórekord/fájlazonosító: **NINCS MEG**. Ha ezt a bináris kézfogást kell bizonyítani, Ghidra-kör kell: `0x00803110` - mely rekordot/indexet teszi az aktív OneUp képforrásává az objektumcsere előtt? A meglévő Ghidra-kimenet az objektumcserét mutatja, a rekordazonosítót nem. [blokkoló]
- A `DAT_00d67914` értéke az Időrend-betöltés alatt, és a floater tényleges megjelenése: **NINCS MEG**; Colab-videón kell mérni a betöltés fázisát és az ablakban látható jelzőt.
- A job-241-től eltérő belépési nézetek általános visszaállítási szabálya: **NINCS MEG**; külön, megnevezett mappából és fotóból belépő mérés szükséges.

**A #6532 „Kész, ha” pontjai ebből a körből:**

- ⛔ Teljes eredeti Picasa Időrend-videó a belépéssel, lapozással, gyűjteményváltással, kártyákkal, billentyűkkel és kilépéssel: itt nem készült, a korábbi részfelvételek teljes lefedettsége nincs igazolva.
- ⛔ Minden megvalósítandó pont bináris címmel igazolva: a jelen négy kérdésből a Space-rekord pontos azonosítása, a progressz futásidejű láthatósága, a `+0x3c4` képtartalma és az általános visszatérési szabály nyitott; a teljes 14 A pontból 12 nyitott.
- ✅ Megvalósítási jegy: az előzmény #6713-at nevezi meg; GitHubot ebben a körben nem ellenőriztem.
- ⛔ Összehasonlító videó vagy képsor a kiadáshoz: nem készült.


#### 38.2.180 A `0x007fe600` kártyamozgás-képlete: második út QEMU-val (#6532, 2026-11-13)

**Hatókör és módszer.** A 38.2.150 §3 a `0x007fe600` mozgásképletét csak utasításolvasattal (A út) vezette le, ezért feltételesnek hagyta. Ez a kör a B utat adja: az eredeti `Picasa3.exe` (3.9.141.259) gépi kódját `qemu-i386` alatt futtattam a privát repó `qemu_harness/hb.py` helyi másolatával. A `0x007fe600`, az időlépést adó `0x009a51b0` és a `_rand` (`0x00c08221`) valódi kódja fut; kézzel épített elem: a `this` (`esi`), a `[this+0x2ec]` rekordtömb (0xf8 bájtos rekordok, a `+0xcc`, `+0xd0`, `+0xd4`, `+0xd8` mezőkkel) és a `[this+0x2f0]` számláló. Helyettesítettem a `QueryPerformanceCounter` (`0xc40298`) és a `QueryPerformanceFrequency` (`0xc404a0`) importot (vezérelt teljesítményszámláló-érték és gyakoriság), valamint a `__getptd` (`0x00bf0583`) függvényt (hamis szálblokk, `+0x14` a `_rand` állapota). Az FPU vezérlőszó `0x27f` (53 bites pontosság), kivéve a §4 külön mérését. A mérés minden esetben a függvény teljes futása a belépéstől a `ret`-ig, nem a közepéről indított szakasz. Az ideiglenes fájlok a munkafa `.bt/` mappájában voltak, a kör végén törölve. A kimenetet a 38.2.150 §3 képletéből írt Python-modellel vetettem össze, bitre (f32 tárolás, f64 számítás).

**Rövid eredmény.**

1. **A képlet igazolt, két úton.** Három ismert bemenetre (egy rekord, három rekord körbefordulással, nagy időlépés), öt számlálóesetre és két hosszú pályára (6 rekord x 200 képkocka, 12 rekord x 300 képkocka, együtt 19 200 érték) az eredeti gépi kód kimenete **minden értékben bitre egyezik** az A úton levezetett képlettel, a `_rand` utána hagyott állapota és a bélyeg is. A 38.2.150 §3 feltételes bekezdése ezzel megerősített.
2. **Három pontosítás az A úthoz,** mindhárom a futtatásból és az újraolvasásból jön: (a) a `T` és a `T * v` szorzatok, valamint az összegek f32-be kerekednek (`0x007fe616`, `0x007fe65a`, `0x007fe668`, `0x007fe676`, `0x007fe68e`); (b) a körbefordítás **egyetlen** hozzáadás vagy levonás tengelyenként, nem ciklus, és a tartomány zárt: 0 és 1 maga marad; (c) a pozíció a **régi** sebességgel lép, a sebesség csak utána kap véletlen járást.
3. **A `[this+0x528]` kezdőértékét a konstruktor írja** (`0x007fa7f0`, `0x007faa31`-`0x007faa41`): egy `QueryPerformanceCounter`-hívás értéke, f64-ként. A 38.2.27 "NINCS MEG"-je ezzel lezárt. Következmény: az első `0x007fe600`-hívás időlépése a qshow létrehozása óta eltelt idő, mert a függvény csak a `Ctrl+F` vagy `Ctrl+B` után fut (38.2.150 §2).
4. **PicasaPy-val összevetve: eltér, de nem felhasználói eltérés.** A PicasaPy-ban nincs kártyánkénti helyzet- és sebességlépés, és nincs `Ctrl+F`/`Ctrl+B` sem. Megvalósítást nem javaslok (§5).

##### §1 A képlet, két úton

| Állítás | A út (utasításolvasat) | B út (QEMU, valódi kód) |
|---|---|---|
| Az időlépés: `T = f32((QPC_most - [this+0x528]) * (1 / QPF))`, másodpercben | `0x009a51b0`: a `QueryPerformanceCounter` értékét f64-be vált (`0x009a51bd`-`0x009a51c0`); ha `[0xd678e8] == 0`, a `QueryPerformanceFrequency` reciprokát számolja és eltárolja (`0x009a51d7`-`0x009a51ec`); `(most - [bélyeg]) * c` (`0x009a51f2`-`0x009a51fc`); a hívó f32-be tárolja (`0x007fe616`) | A valódi `0x009a51b0` futott, három gyakorisággal (3 579 545, 10 000 000 és 1 000 000 ütem/s) és vezérelt teljesítményszámlálóval: az időlépés f32-ben bitre egyezik a képlettel (B1: 0,0166666433; B2: 0,100000001; B3: 1,70000005) |
| A rekordok száma `n = [this+0x2f0] >> 1`; `n == 0` esetén a bélyeg akkor is frissül | `0x007fe61c` `test [esi+0x2f0], 0xfffffffe`, `jbe 0x7fe7a5`; ciklusszámláló `0x007fe78f`-`0x007fe799`; a bélyeg tárolása `0x007fe7aa`-`0x007fe7b6` a ciklus után, a kapu ugrása is ide érkezik | Számláló 0, 1, 2, 3, 5: rekordszám 0, 0, 1, 1, 2; a többi rekord érintetlen; a `_rand` állapota 0 és 1 számlálónál változatlan, 2 és 3 esetén két, 5 esetén négy hívással lép; a bélyeg mind az öt esetben az új mérőállás |
| Pozíció: `x = f32(x + f32(T * vx))`, `y = f32(y + f32(T * vy))`, a **régi** sebességgel | `0x007fe650`-`0x007fe696`: a szorzatok `0x007fe65a`-ba és `0x007fe668`-ba f32-ként tárolódnak, az összegek `0x007fe676`-ba és `0x007fe68e`-be, majd a rekordba | B1: `x = 0,501666665` (0,5 + 0,0166666433 * 0,1), `y = 0,499166667`; a sebesség az új értékével (`0,0995012522`) csak a lépés után látszik |
| Körbefordítás tengelyenként legfeljebb egyszer: `x < 0`: `+1`; `y < 0`: `+1`; `x > 1`: `-1`; `y > 1`: `-1`; a 0 és az 1 maga marad | `0x007fe69e`-`0x007fe6fc`: `fcom` a 0-val (`jp` átugorja a hozzáadást, ha nem kisebb), majd az 1-gyel (`jp` átugorja a levonást, ha nem nagyobb); a négy `jp`: `0x007fe6a5`, `0x007fe6bc`, `0x007fe6d9`, `0x007fe6f4` | B2: `0,99 + 0,05 = 1,04 -> 0,04`; `0,01 - 0,03 = -0,02 -> 0,98`; a `(1,0; 0,0)` rekord helyben marad. B3: `0,2 - 1,53 = -1,33 -> -0,33` és `0,9 + 1,36 = 2,26 -> 1,26`, vagyis egyszeri korrekció után is a tartományon kívül marad |
| Véletlen járás: `vx += u1 * 0,001 - 0,0005`, majd `vy += u2 * 0,001 - 0,0005`, `u = r / 32768`, rekordonként ebben a sorrendben; f32-ben tárolva | `0x007fe713`-`0x007fe78d`: `_rand`, `(r + 0x3f8000) << 8` mint f32, `- 1,0` (`0xc7e328`), `* 0,001` (`0xcf3db0`), `- 0,0005` (`0xcf4858`), `+ [rekord]` | A `_rand` állapota három magnál (1, `0x3039`, `0xdeadbeef`) és a hosszú pályákon bitre a modell szerint lép, rekordonként két hívással, az index szerinti sorrendben |

##### §2 A három ismert bemenet és a mért kimenet

A bemenet f32-ként került a rekordba. Az időlépést a teljesítményszámláló különbsége adja.

| Eset | Bemenet (`x`, `y`, `vx`, `vy`) | Mag | Időlépés | Kimenet (QEMU, a modell ugyanezt adja) |
|---|---|---:|---:|---|
| B1 egy rekord | 0,5; 0,5; 0,1; -0,05 | 1 | 0,0166666433 (59 659 ütem, 3 579 545 ütem/s) | 0,501666665; 0,499166667; 0,0995012522; -0,0499364324; mag utána 3 357 800 067 |
| B2 rekord 0 | 0,99; 0,01; 0,5; -0,3 | `0x3039` | 0,100000001 (1 000 000 ütem, 10 000 000 ütem/s) | 0,0399999619; 0,980000019; 0,499731451; -0,299915165 |
| B2 rekord 1 | 0,2; 0,8; -0,9; 0,9 | | | 0,110000007; 0,889999986; -0,899712801; 0,900175154 |
| B2 rekord 2 | 1,0; 0,0; 0,0; 0,0 | | | 1; 0; -0,000322143547; 0,000214263913; mag utána 3 681 394 607 |
| B3 nagy időlépés | 0,2; 0,9; -0,9; 0,8 | `0xdeadbeef` | 1,70000005 (1 700 000 ütem, 1 000 000 ütem/s) | -0,329999924; 1,25999999; -0,899940372; 0,800016344; mag utána 1 108 892 897 |

Minden bemenet után az x87 verem üres (az állapotszó `TOP` mezője 0, csak a pontossági jelző áll), tehát a függvény nem szivárogtat lebegőpontos veremet.

##### §3 Hosszú pálya, pontosság és kezdőérték

- **Hosszú pálya (B5).** 6 rekord, 200 képkocka, 3 579 545 ütem/s, ingadozó képkockaidővel (a 60 kép/mp 70-130 százaléka), magja 1: 4800 érték, mind egyezik. 12 rekord, 300 képkocka, 10 000 000 ütem/s, magja 777: 14 400 érték, mind egyezik. Minden képkockában a bélyeg és a `_rand` állapota is egyezik.
- **A pontossági vezérlőszó (B6).** `0x27f` (53 bit) és `0x37f` (64 bit): a két futás azonos, 0 eltérő érték. `0x07f` (24 bit): a 4800 értékből 3319 különbözik, a legnagyobb eltérés 6,02e-05 az egységnégyzetben. A futó Picasa vezérlőszava nincs mérve; a képlet a `0x27f`/`0x37f` esetben bitre pontos, a `0x07f` esetben legfeljebb ennyi a szórás. Megvalósításhoz ez nem számít.
- **A kezdőérték hiánya (B8).** Ha a bélyeg 0, és a teljesítményszámláló 1 000 000 000 000 (279 365 s időlépés), az első lépés után `x = 27 936,0137`, `y = -13 966,7568`: az egyetlen körbefordítás nem hozza vissza az egységnégyzetbe. A konstruktor `0x007faa31`-`0x007faa41` tárolása ezt zárja ki, a valódi első időlépés a qshow létrehozása óta eltelt idő. A rajzút `y`-t egy helyen lineárisan használja (`0x007fea80`-`0x007feaac`), ezért a tartományon kívüli érték látható hatása nincs mérve.

##### §4 Kontroll: a mérőpad érzékeny a kódra

Ha egy mérés csak zöld, az még nem mér. Ezért a kódot átírtam, és a modellel összevetettem:

| Átírás | Eredeti kód | Átírt kód |
|---|---|---|
| `0x007fe6a5` `jp` -> `jmp` (az `x < 0` ág kiesik), bemenet `x = 0,01`, `vx = -0,5` | 4/4 érték egyezik | 3/4 egyezik, eltér |
| `0x007fe6bc` `jp` -> `jmp` (`y < 0`), bemenet `y = 0,01`, `vy = -0,5` | 4/4 | 3/4, eltér |
| `0x007fe6d9` `jp` -> `jmp` (`x > 1`), bemenet `x = 0,99`, `vx = 0,5` | 4/4 | 3/4, eltér |
| `0x007fe6f4` `jp` -> `jmp` (`y > 1`), bemenet `y = 0,99`, `vy = 0,5` | 4/4 | 3/4, eltér |
| `0xcf3db0`: 0,001 -> 0,002 | 8/8 | 4/8, eltér |
| `0xc7e328`: 1,0 -> 0,5 | 8/8 | 6/8, eltér |

Mind a hat átírás eltérést ad, tehát a mérőpad látja a kódot, és a négy körbefordító ág mindegyikét a megfelelő bemenet ténylegesen érinti. (Az első kísérletemben két ágat olyan bemenettel írtam át, amely az ágat nem érintette; az a két sor nem bizonyított semmit, és kikerült a fenti táblából.)

##### §5 Összevetés a PicasaPy-val és megvalósítási javaslat

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `0x007fe600` a rekordok helyzetét (`[0, 1]` tórusz) és sebességét képkockánként lépteti, véletlen járással; csak `Ctrl+F` vagy `Ctrl+B` után fut (38.2.150 §2). | `timeline_motion.py` (423 sor) nem tartalmaz kártyánkénti helyzet- és sebességlépést; a `card_stack_offset` (`timeline_motion.py:100-131`) statikus, indexmagos eltolás, a `TimelinePanel.qml:250-260` ezt írja a kártyaköteg `x`, `y` mezőjébe. A panelben nincs időzítő vagy animáció; a `TimelineView.qml:333` 16 ms-os időzítője a lapozó pályát és a háttér átúszását hajtja, nem a kártyák sodródását. A `TimelineView.qml:393-406` csak az Escape, jobbra, balra és Space billentyűt kezeli. | **Eltér, de nincs felhasználói következménye:** a PicasaPy-ban a rejtett mód nincs meg, az alap Időrendben pedig az eredeti sem mozgat semmit. |

**Javaslat (a hívónak, kódot nem módosítottam).**

1. **Termékkódhoz ne nyúlj.** Az alap Időrend nem hívja a `0x007fe600`-at, a rejtett mód nem szerepel az eredeti felhasználói felületén, és a PicasaPy `card_stack_offset` statikus eltolása nem ennek a mozgásnak a megfelelője. A 38.2.150 §5 javaslata (a `timeline_motion.py:100-110` docstring téves hivatkozásának javítása) változatlanul él, ehhez ez a kör nem tesz hozzá.
2. **Ha a tulajdonos a rejtett módot kéri,** a Qt-mentes lépés a `timeline_motion.py`-ba kerülne. Bemenet: a rekordok `(x, y, vx, vy)` f32 értékei, az `n` és a `T`. Lépés rekordonként, sorrendben: `x = f32(x + f32(T * vx))`, `y = f32(y + f32(T * vy))`; `x < 0`: `x += 1`; `y < 0`: `y += 1`; `x > 1`: `x -= 1`; `y > 1`: `y -= 1` (mindegyik legfeljebb egyszer, a 0 és az 1 maga marad); majd `vx = f32(vx + (u1 * 0,001 - 0,0005))`, `vy = f32(vy + (u2 * 0,001 - 0,0005))`, ahol `u` egyenletes `[0, 1)`. A `T` másodperc, a lépés a bélyeg frissítésével zárul, `n == 0` esetén is. Elfogadási próba: a §2 B1-B3 sorai ellenőrző értékek (a bemenet, az időlépés és a `_rand` sorozat adott). A pontos véletlen sorozat nem elvárás: a qshow a szál `_rand` állapotát folytatja (38.2.150 §1), így bitre azonos sorozat nem várható el, csak az `[-0,0005; 0,0005)` egyenletes eloszlás.
3. **A képlet önmagában nem elég a látható viselkedéshez.** Akadály, pontosan körülhatárolva: (a) a hívás üteme (`0x00800a30` hívója: nincs meg); (b) a rajzút `(x, y)` leképezése: a `0x007fe7c0` az `x` és `y` mezőt `2π`-vel szorozza és a `0x00c29d20` függvénybe adja (`0x007fe81c`-`0x007fe863`, `0x007fea0c`-`0x007fea2f`); a QEMU hét bemenettel megmutatta, hogy a `0x00c29d20` koszinusz (`cos(0) = 1`, `cos(π/2) = 0`, `cos(π) = -1`, `cos(2π) = 1`, `cos(0,628) = 0,809`, `cos(7,854) = 0`, `cos(-1,885) = -0,309`), de a rajzút többi része, köztük az `y` lineáris használata (`0x007fea80`), nem futott; (c) a `Ctrl+F` és a `Ctrl+B` külön jelentése (a kapu mindkettőre ugyanúgy nyit); (d) a valódi FPU vezérlőszó és a valódi teljesítményszámláló a futó programban. A következő irány megnevezve: a `0x007fe7c0` rajzút futtatása vagy Colab-felvétel `Ctrl+F` lenyomásával az Időrendben (nem készült).

##### Nyitott kérdések mérlege

Nyitott kérdések: 4 nyílt · 3 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 "csak nyitva"

| Kérdés | Állapot | Mi kell hozzá |
|---|---|---|
| A `0x007fe600` mozgásképletének második útja (QEMU) | **LEZÁRVA** (§1-§4) | |
| A `[this+0x528]` kezdőértéke | **LEZÁRVA** (a konstruktor írja, §3) | |
| Az időlépés képlete a valódi `0x009a51b0`-val | **LEZÁRVA** (§1, három gyakorisággal) | |
| A `0x007fe600` hívási üteme | **NYÍLT**, a rejtett mód miatt alacsony prioritás | A `0x00800a30` hívója, a periodikus hívás. |
| A `0x007fe7c0` rajzút leképezése `(x, y)`-ból képpé | **NYÍLT**, alacsony prioritás | A rajzút futtatása; az `y` lineáris használata (`0x007fea80`-`0x007feaac`). |
| A `Ctrl+F` és a `Ctrl+B` külön jelentése | **NYÍLT**, alacsony prioritás | A `[this+0x3bc]` és a `[this+0x3bd]` külön fogyasztóinak olvasása a `0x007fe7c0`-ban. |
| A valódi FPU vezérlőszó és teljesítményszámláló a futó programban | **NYÍLT**, alacsony prioritás | Colab-futás naplózással; a hatás legfeljebb 6e-05 az egységnégyzetben. |

##### Amit kizártam

- **"A körbefordítás ciklussal visszahoz a `[0, 1]` tartományba"**: cáfolt (B3: `-0,33` és `1,26` marad; B8: `27 936` marad).
- **"A pozíció a frissített sebességgel lép"**: cáfolt (B1, bitre).
- **"A bélyeg csak nem üres listánál frissül"**: cáfolt (számláló 0 és 1: a bélyeg frissül, rekord és `_rand` nem).
- **"A `[this+0x528]` kezdőértéke 0"**: cáfolt (konstruktor, `0x007faa41`).
- **"A `0x00c29d20` szinusz"**: cáfolt (QEMU: koszinusz).

##### Bizonyítottság

**Megerősített:** a `0x007fe600` teljes lépésképlete (időlépés, pozíció, körbefordítás, véletlen járás, rekordszám, bélyegfrissítés) két úton: utasításolvasat és az eredeti gépi kód futtatása, 19 200 bitre egyező érték a hosszú pályákon, a hat átírásos kontroll eltérést ad. **Feltételes:** a rajzút leképezése, a hívás üteme, a `Ctrl+F`/`Ctrl+B` külön jelentése, a futó program FPU vezérlőszava és teljesítményszámlálója (a mérés vezérelt teljesítményszámlálóval és hamis szálblokkal futott, a rekordok kézzel épültek; Windows alatti futás nem volt).

#### 38.2.190 Az Időrend kártyáinak forráscsoportjai és a kártyadátum írója (#6532, 2026-11-13)

**Hatókör és módszer.** Két blokkoló kérdés: (1) a `0x006dc4c0` által a `0x004b8ee0` → `0x004b8470` → `0x004b29d0` láncnak átadott `CThumbUI+0x2c0` objektum (`CAlbumState`) mely sorai jutnak a qshow `+0x3a8` kártyalistájába, és milyen sorrendben; (2) melyik út írja a `0x0044f7c0` getter által olvasott dátumtömböt, és mit tárol. **A út:** a friss Ghidra-kimenet (`picasapy-agent/referencia/ghidra/2026-11-13-6845-6532-colab-decomp.txt`, az öt kért cím), a korábbi kimenetek (`2026-11-11-6532-colab-decomp-3/-5/-9/-10.txt`) és utasításszintű olvasat (`pe_dis.py`, `picasa_dis.py`); két teljes `.text` pásztázás a `paszta.py` kapujával (`+0x162` bájtra író utasítás, `+0xd8` dword-írás; csúcs 42 MiB). **B út:** az eredeti Picasa saját adata (`research/testdata`: három katalógus `db3` mappája, `albumdata`, `catdata`, `thumbindex.db`) a PicasaPy `pmpimport` olvasóival, és a job-239 felvétel dokumentált tényei (38.2.81). Becsült értéket nem használtam.

##### §1 A lánc: mi jut át a `+0x2c0` objektumból a kártyalistáig (A út)

1. **Átadás.** `0x006dc626`-`0x006dc62c`: `EAX = [EBP+0x2c0]`, hívás: `0x004b8ee0`. A `0x006dc4c0` (az első paraméter a `CThumbUI`, 38.2.108) hívói közt van a `0x004afcb0` (`0x004afd3c`; ez előbb a `0x004aae90`-et hívja, `0x004afd1a`) és a `0x004b07c0` (`0x004b0803`), tehát a lista a főablak minden állapotváltozásakor újraépül.
2. **Sorok.** A `CAlbumState` `+0x138` mutatójú, `0x24` bájtos sorai az albumtábla sorai: ugyanaz a sorszám megy a `CThumbDB` oszlopolvasóinak (`+0x14` fájlnév, `+0x18` név, `+0x20` dátum, `+0x28` token; a kategóriát a `0x0044ddd0` adja). Az oszlop-objektumok a `CThumbDB`-ben: `token +0xaf0`, `name +0xb50`, `filename +0xbb0`, `date +0xc10`, `category +0xc78` (konstruktor: `0x004158ee`-`0x00415999`, a kulcsszövegek `0x00c80d68`, `0x00c7fa20`, `0x00c80d70`, `0x00c80d7c`, `0x00c80d84`); az albumtábla az `+0x988`, a kategóriatábla (`catdata`) a `+0x760` címen (`0x00415866`, `0x004158c9`). A virtuális albumokat a `0x004abe70` hozza létre (`0x004ad220` hívásai: `]star`, `]screensaver`, `]updated`, `]history:email`, `]history:upload`); a `0x004ad220` alapértelmezett kategórianeve a `Labels` (`0x004ad286`, sztring `0x00c7ec5c`).
3. **Sorszámlista.** `0x004b8ee0` minden sort, amelynek `+0x0c` állapota nem nulla, felvesz a `+0x148` sorszámlistába, majd a `0x004baaa0` rendezi (`0x004a7890` összehasonlítóval), és hívja a `0x004b8470`-et (`0x004b9192`).
4. **Rekordlista.** `0x004b8470` üríti a `+0x158` listát, hívja a `0x004b80d0`-t (társgazda- és nyilvános gazda-rekordok, 2-es és 9-es típus), majd sorszámonként a `0x004b29d0`-t, ha a `+0x9d` (`folderview`, 38.2.108) nulla, vagy a `0x004461a0` igaz (`0x004b85a0`-`0x004b85c8`); a fa nézetben (`+0x9d` nem nulla) a mappákat a `0x004b6190` hozza (5-ös, 8-as, 2-es típus, 38.2.112), ezek nem kártyák.
5. **A kártyarekord.** `0x004b29d0`: a sor `+0x0c` állapota 2 kell legyen, különben nincs rekord (`0x004b2a1a`, 38.2.110). Ezután a kategória a `0x0044ddd0`-val (`0x004b2a11`); kategóriaváltáskor fejlécrekord (`0x004b2e10`, 3-as típus, `0x004b2a29`-`0x004b2a40`); ha a környezetrekord `+0x00` mezője egyenlő a sor kategóriájával, a sor kimarad (`0x004b2a49`-`0x004b2a4c`); különben a `0x004a0720(1, sor, 0, ...)` hívás az 1-es típusú rekordot adja (`0x004b2aa3`-`0x004b2ab4`).
6. **A kártyalista.** A qshow `0x007fc7c0` csak az `+0x30 == 1` és `+0x18 == 0` rekordokból vesz sort (38.2.110); az 1-es típusú, nulla `+0x18`-as rekord egyedül a `0x004b29d0`-ból jön (38.2.112), tehát **minden `0x004b29d0`-rekord kártya**. A dátumot a sorszámhoz a `0x0044f7c0` adja (`IThumbDB +0x20`), a kártyarekord tartalmát a `0x004ae430` és a `0x007fa5b0` állítja elő; a `0xf8` bájtos kártyák a qshow `+0x3a8` listájába kerülnek (a függvényben `+0xb0`/`+0xb4`).

##### §2 Mely sorok jutnak 2-es állapotba (az `+0x0c` állapotgép)

Az állapot írója a `0x004ab520`; átmenetek: `0x004a8bb0` (1 → 3, 2 → 4), `0x004a8bf0` (3 → 1, 4 → 2). A 0 → 1 lépést a `0x004aa9f0` adja, az 1 → 2 lépést a `0x004aae90` (a `0x004b0190` nézetlekérés sikere esetén; Ghidra: `2026-11-11-6532-colab-decomp-10.txt`). A sorrekord mezői, amelyek a döntésben részt vesznek:

| mező | érték és forrás |
|---|---|
| `+0x1a` érvényes | első kiértékelésnél a név (`IThumbDB +0x18`, `name` oszlop) nem üres és nem `root` (`0x004aab27`-`0x004aabaa`, a `root` sztring `0x00c817d4`); különben állapot 0 és a sor végleg kimarad |
| `+0x18` album | a fájlnév üres (`0x004461a0`, `IThumbDB +0x14`) |
| `+0x00` virtuális | a token nem üres, és nem `]album:`-nal (`0x00c811c4`) és nem `]facealbum:`-nal (`0x00c83408`) kezdődik (`0x004aca00`; az előtag-összehasonlító `0x00987030`) |
| `+0x19` | a `0x004aa9f0` elején nullázza (`0x004aaa46`) |

Döntés (`0x004aac38`-`0x004aae67`; a `CAlbumState` `+0x162` és `+0x310` jelzője nulla, vagyis nincs keresés):

- **Felhasználói album** (album, nem virtuális): 2-es állapotba jut, ha a nézetlekérés sikeres (a tagsági listák megvannak); az elemszám nem számít, az üres album is 2-es állapotot kap (`0x004aae90`: üres tagságnál `+0x14 = 1`, állapot 2). A `+0x162` vagy a `+0x310` bekapcsolt állapotában az album a mappa szabályát követi (`0x004aac7a`-`0x004aac96`: a `+0x15` jelző nullázódik).
- **Mappa és virtuális album:** a tagság elemszáma nagyobb nulla, a dátum nem nulla (nulla dátumnál a `0x00441ac0` automatikus dátumot próbál adni, `0x004aadc9`, 3. szakasz), és a `0x004afd60` nulla értéket ad (nem üres elemlista és jelzőtömb; a `+0x167` jelzőnél legalább egy tagnak 1 jelzőbájtja kell; a `+0x167` jelentése nincs meg). Ez a feltétel a gyakorlatban a nem üres tagságra szűkül.
- **Sor a kategóriája miatt kimarad** (§1/5), ha a kategória lecsukott: a `0x004b2e10` a `0x004b3443`-`0x004b3469` címeken a környezetrekord `+0x00` mezőjét -1-re állítja (látható), ha a `catdata` `state` bájtja nem nulla (`0x004b3211`-`0x004b3226`: `0x006a5e60(CThumbDB+0x760, "state", kategória)`; sztring `0x00c817f0`) és a `+0x1d` jelző nem nulla; különben a kategória azonosítójára (rejtett). Keresési módban (`CAlbumState+0x162` nem nulla) a `state` nem számít (`0x004b3232`-`0x004b3256`: csak a `catdata` `info` oszlopa, `0x004ab5e0`, `0x00c812cc`, zárhatja ki).
- A `+0x162` az **egyetlen** bájtra író utasítás a teljes `.text`-ben a konstruktoron (`0x004a17d6`) kívül a `0x00662c53`: a keresési kezelő `0x00662b20` (sztringek: `Search results for "%s"`, `CThumbUI::searchmatchstr`, `%d results: `) állítja, tehát **keresési mód jelző**.

##### §3 B út: valódi katalógus és felvétel

**A `category` oszlop a `catdata` sorára mutat.** Az `albumdata_category.pmp` 0-19 közti értékei a 20 soros `catdata` sorszámai (`research/testdata/Picasa2/db3`, 2371 `albumdata`-sor). Egyező példák: a 12-es kategória `Csilla` (47 sor, pl. `2014-01-25 Csilla kreatív dolgai`), a 13-as `Camera` (3 sor, `Instagram SGS3`), az 5-ös `Exported Pictures` (3 sor, `... export`), a 14-es `Downloaded Albums~sipos.aniko13` (2 sor, `Ovis Farsang...`), a 0-s `Labels` (41 sor: 7 virtuális token, 17 `]album:` felhasználói album fájlnév nélkül, 18 üres token- és nevű, `949998.0` dátumú sor), a 2-es `Folders on Disk` (2063 sor), a 8-as `People` (`]unknownface`, `Név nélküliek`), a 7-es `Hidden Folders` (1 sor). A `0x004ad220` `Labels` alapértelmezése (§1/2) ugyanezt a kapcsolatot adja a binárisból.

**A `state` oszlop a gyakorlatban nulla is.** A tulajdonos katalógusában a `Labels` `state = 0` (lecsukott), minden más kategória 1; a `Picasa2-arcok` katalógusban két mappakategória (`PicasaPy-golden-kit`, `PicasaPy-merokit`) 0. Ebből a katalógusból az Időrendben **nem lenne** albumkártya, ha a §2 szabálya érvényes.

**A job-239 felvétel egyezik a szabállyal** (38.2.81, `pmp-database.md` 4551. sor környéke): a kártyák: négy fixture-mappa, `PicasaTeszt`, `Recently Updated` (mind tagsággal, kibontott csoportokban); az `Unnamed` (`]unknownface`, nincs tagja) sor nem kártya. Két másik futás tárolt dátumpárja (`pmp-database.md`, 4551. és 4617. sor, nem a job-239 saját adata) szerint a `Recently Updated` dátuma mindkét futásban nagyobb, mint a `PicasaTeszt`-é (`46309,3385` és `46309,3243` a `46309,3217` ellen; `46309,4432` és `46309,4455` a `46309,4430` ellen), ami a látott PicasaTeszt → Recently Updated sorrenddel egyezik. Ez **egyezés, nem bizonyíték** a lecsukott kategóriára és a fa nézetre: ilyen felvétel nincs.

##### §4 A kártyák sorrendje

A `0x007fc7c0` a kártyák sorszámaihoz a dátumot a `0x0044f7c0`-val olvassa (`+0x88` tömb), a `0x007fc4c0` a `0x0049cd60`-nal **növekvő `double` kulcs szerint, alulról felépülő összefésüléses rendezéssel** állítja sorrendbe (sorszámok permutációja a `+0x98` tömbben). A rendezés **stabil**: az első menetek egyenlőségnél nem cserélnek (`<` csere, illetve `<=` megtartás, `0x0049cd60`), az összefésülő `0x0049ecd0`-t nem vizsgáltam. Azonos dátumnál ezért a `+0x148` sorszámlista sorrendje dönt, amit a `0x004baaa0` a `0x004a7890` összehasonlítóval állít elő (a kulcs nincs azonosítva). Valódi példa azonos dátumra: a `]screensaver`, `]updated`, `]history:email`, `]history:upload` sor mind `45772,771782407406` (a tulajdonos katalógusában).

A rendezés **után** a `0x007fc4c0` a `+0x88` tömb minden elemét dekódolja (`0x0098b320`), két mezőjét kiolvassa (`0x0098ba30` → `+0x10`, `0x0098b9e0` → `+0x14`), majd újrakódolja a `0x0098b550(1, 0, 0, 0, ...)` hívással (`0x007fc510`-`0x007fc562`). A kártyarendezést ez nem érinti (az sorszámlista már kész); a mezők naptári jelentése nincs azonosítva (feltevés: hónap első napja, nem bizonyított).

##### §5 A dátumtömb: ki írja, és mit tárol

**A út (a getter és az író ugyanaz az oszlop).** A `0x0044f7c0` az `IThumbDB` `+0xc20` mezőjén át a `date` oszlop gyorsítótárának `+0x234` tömbjéből olvas: `[tömb+0x48] + sor*8`, az elemszám `[+0x4c] >> 1`, határon kívül a `+0xc28` tartalék (Ghidra: `0x0044f7c0`; `IThumbDB` = a teljes objektum `+0x48`). Az oszlop a `CThumbDB` konstruktorában születik: kulcs `date` (`0x00c80d7c`), kezelő tábla `ebp+0x988` (`0x00415950`-`0x0041596f`, `0x00495d30`). Az író a `IThumbDB` vtábla **3. rése, `0x004460a0`** (`0x00c81fb0`; thunk `0x0049f390`): `0x004460c3`-`0x004460d8` a `0x006a5c60(tábla = IThumbDB+0x940 = teljes+0x988, "date", sor, double)` hívás. A `0x006a5c60` a `0x006a41e0(tábla, név, 0x13320002)` hívással ugyanazt a gyorsítótár-bejegyzést keresi meg, amelyet a getter lusta betöltője (`0x00499650`) is, majd a `+0x234` tömbbe ír (`0x006a5d95`-`0x006a5db1`: `fcom [tömb+sor*8]`, azonosnál kihagyja, különben `fstp [tömb+sor*8]`; módosítás-jelzés `0x006a2a60`). **Ugyanaz a tábla, ugyanaz a név, ugyanaz a tömb: az író megerősített.**

**Ki hívja az írót (az index pozitív találatai; kimerítő lista nincs):** a `0x00441ac0` (`0x004aa9f0` sorfrissítés, `0x00441e00` mappafelvétel a `Folders on Disk` és `Other Stuff` sztringekkel, `0x0055d320` átnevezési ág), a Mappa-tulajdonságok `autodate` kezelője (`0x00849dc0` → `0x00441760`), és az online album (`0x006f2fc0`, DB és ini is; `pmp-database.md`, 12. szakasz). A `0x00441ac0` (disszasszemblálva): a getterrel olvassa az aktuális dátumot; **ha az pontosan nulla**, a `0x00441760`-nal számolja az automatikus értéket (kezdőérték `949998.0`, `0x00c7ccf8`), és sikernél a 3. réssel írja, `bool = 0` (csak DB, ini nem). A `0x00441760` a mappa elemeinek **legkisebb** 64 bites időértékét veszi (`0x004419d6`-`0x004419e6`, a `0x004edf60` rekordlekérő mezője), és a `0x0098b650` alakítja `double`-ré: `FileTimeToSystemTime` → `SystemTimeToTzSpecificLocalTime(NULL)` → `Ordinal_184` (helyi `SYSTEMTIME` → változatidő).

**B út (a tárolt érték = a legkorábbi képidő, helyi időre váltva).** Mérés a tulajdonos katalógusán: minden `albumdata` sor, amelynek `filename` mappájában a `thumbindex.db` talál képet (2305 sor; a `thumbindex` 1. időbélyege, a kép metaadat-dátuma, UTC-ként értve, `Europe/Budapest` helyi időre váltva, a mappa minimumához hasonlítva, ±1,5 s tűréssel):

| katalógus | összehasonlítható sor | pontos egyezés a minimummal | tárolt későbbi | tárolt korábbi |
|---|---:|---:|---:|---:|
| `Picasa2/db3` | 2305 | **1983 (86,0%)** | 207 | 115 |
| `Picasa2-arcok/Picasa2/db3` | 110 | 72 (65,5%) | 38 | 0 |
| `1557-masolat-mentese/db3-utana/db3` | 108 | 71 (65,7%) | 37 | 0 |

Az időzóna-váltás nélkül a pontos egyezés 0, az eltérés pontosan 1 óra télen és 2 óra nyáron: ez a `0x0098b650` helyi időre váltása. **A tárolt érték tehát első beíráskor a legkorábbi képidő, utána nem számolódik újra** (a "később" és "korábbi" eltérések a mappa tartalmának utólagos változásából vagy kézi beállításból adódnak: `.picasa.ini` `date=`, Mappa-tulajdonságok). A `pmp-database.md` korábbi "0/23 egyezik a legkorábbi képidővel" mérése a teljes katalógusos méréssel nem egyeztethető össze, ha ugyanazt az egyenlőséget vizsgálta; a mostani mérés időzóna-helyes és 2305 sorra fut. A felhasználói albumok (`]album:` fájlnév nélkül) és a virtuális sorok dátumának forrása **nincs mérve**: a virtuális sorok dátuma létrehozási bélyegnek látszik (négy sor azonos `45772,771782407406`), az albumsorok forrása (ini `[.album:token] date=` vagy első tag) a tagságadat hiányában nem vethető össze.

**Mit tárol a kártya?** A kártya dátuma a sor **tárolt `albumdata_date` értéke** (OLE-változatidő, napok 1899-12-30 óta, a nap törtrésze az idő, helyi időben): mappánál az első beíráskor a legkorábbi képidő (vagy a `.picasa.ini` `date=` értéke, vagy kézi beállítás), nem a mappa fájlrendszer-ideje és nem az élő legkorábbi kép. A dátumsáv két vége (`0x007fee70`, 38.2.103) a rendezett lista **első és utolsó kártyájának** ugyanez a dátuma, nem a képek globális szélsőértéke.

##### §6 Összevetés a PicasaPy-val és megvalósítási javaslat

| Eredeti | Nálunk | Eredmény |
|---|---|---|
| A kártya = a lista minden 2-es állapotú sora: mappa (nem üres tagsággal), felhasználói album (üres is), virtuális album (nem üres tagsággal); a lecsukott kategória és a fa nézet kihagyhat sorokat (§1, §2). | Mappa: a látható fotókból; album: az `albums_in_index` nem üres sorai (`timeline_controller.py:218-247,269-291`). Virtuális album nincs. Kategóriaállapot és fa nézet nincs. | **eltér a virtuális albumokban** (a `Recently Updated` hiányzik, 38.2.81 szerint kártya); **egyezik a mappákban**; a kategória- és nézetfeltétel hatása **nem dönthető el** futásidőben (§3). |
| A kártyadátum a tárolt `albumdata_date`: első beíráskor a legkorábbi képidő, utána állandó (§5). | A legkorábbi `taken_at` az élő, látható fotók közül (`timeline_controller.py:341-382`), fájlidő-tartalék nélkül. A `folders.date` (`index/sync_photos.py:202-240`: ini `date=` elsőbbség, különben a legkorábbi `taken_at_override`/`taken_at`/befagyasztott fájlidő) megvan az indexben, az Időrend nem használja. | **eltér:** az eredeti perzisztens dátumot használ (a mért katalógusban 14% eltérés a mai legkorábbi képidőtől), nálunk a dátum élő. |
| A dátumsáv két vége az első és az utolsó kártya dátuma. | A sávszélek az összes látható fotó EXIF-szélsői (`timeline_controller.py:223-231,301-333`). | **eltér:** az utolsó kártya a mappa **legkorábbi** idejét viseli, nálunk a legkésőbbi fotóét. |
| Azonos dátumnál a stabil rendezés a `+0x148` sorrendet tartja (kulcsa nincs meg). | Dátum, név (kisbetűs), azonosító (`timeline_controller.py:293-299`). | **nem dönthető el** (a `0x004a7890` kulcsa). |

**Javaslat a hívónak (kódot nem módosítottam).** Csak a bizonyított pontok:

1. **Mappakártya dátuma:** a `folders.date` (a `collage_album_fields.folder_date_iso` már olvassa, `collage_album_fields.py:65`) legyen az elsődleges dátumkulcs, a legkorábbi `taken_at` csak tartalék; az albumkártyánál az `albums.date`, tartaléka a legkorábbi tag. A rendezés maradjon teljes időponton (az eredeti `double` kulcs napszakot is tartalmaz, 38.2.108). A `folders.date` élő számítású, az eredeti első beírás után állandó: a felhasználói különbség csak azoknál a mappáknál várható, amelyek képei utólag változtak (a mért katalógusban 14%).
2. **A dátumsáv két vége** a rendezett kártyalista első és utolsó kártyadátumából jöjjön, ne az összes fotó szélsőiből.
3. **A virtuális albumok** (`Recently Updated`, `Starred`, `Screensaver`, `Emailed`, `Uploaded`) kártyáját **ne** adja hozzá a fejlesztő, amíg a dátumuk forrása nincs meg (§5, utolsó pont): becsült dátummal az eredeti sorrendje nem reprodukálható.
4. **A lecsukott kategória és a fa nézet hatását** ne valósítsa meg, amíg a Colab-mérés (lent) nem készült el.

**Kész, ha** (a hívó által kiadott fejlesztői jegyhez):

- [ ] a mappakártya dátuma a `folders.date`, és egy teszt egy ini `date=` értékű mappán az ini dátumát adja (nem a legkorábbi képét);
- [ ] a dátumsáv két vége az első és az utolsó kártyadátum, teszttel olyan katalógusra, ahol az utolsó kártya mappájában van a legkésőbbi fotónál korábbi dátumú kép;
- [ ] a rendezés kulcsa teljes időpont, azonos dátumnál megnevezett, dokumentált tartaléksorrenddel;
- [ ] vizuális egyezés: az eredeti `job-239` kártyasorrendje (4 fixture-mappa, `PicasaTeszt`) változatlan.

**Mérési feladat (Colab, 1 feladat, a hívó adhatja fel):** Ctrl+5 három állapotban ugyanabban a katalógusban: (a) lapos mappanézet, a `Folders on Disk` csoport lecsukva; (b) fa mappanézet; (c) minden csoport kibontva, lapos nézet. Mérés: a kártyák neve és sorrendje. Ez dönti el a §2 lecsukási szabályának és a `+0x9d` szűrésnek a hatását.

##### Nyitott kérdések mérlege

Nyitott kérdések: 7 nyílt · 3 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 "csak nyitva"

| Kérdés | Állapot | Mi kell hozzá |
|---|---|---|
| A `+0x2c0` objektumból a kártyalistáig vezető lánc és a sorok forrása (mappa, album, virtuális) | **LEZÁRVA** (§1-§3) | |
| A getter által olvasott dátumtömb írója | **LEZÁRVA** (§5: `0x004460a0` → `0x006a5c60`) | |
| A mappakártya dátuma | **LEZÁRVA** (§5: első beíráskor a legkorábbi képidő, utána tárolt; 86,0%/65,5%/65,7% pontos egyezés) | |
| A lecsukott kategória és a fa nézet futásidejű hatása a kártyákra | **NYÍLT** | A fenti Colab-mérés. |
| A `0x004b2e10` `+0x1d` jelzőjének forrása | **NYÍLT** | Ghidra-kör kell: `0x004a4710` - a `CAlbumState+0xe4`/`+0xe0` objektum és a `0x004143c0` keresés jelentése (kategórianév egy halmazban). |
| A `CAlbumState+0xd8` nézetmód értékei | **NYÍLT** | Ghidra-kör kell: `0x005d9cc0` - melyik parancs milyen módot állít a `0x004b07c0`-nal; a `+0xd8 == 3` ág nem hívja a fejlécépítőt (`0x004b2a2c`), így a kategóriarejtés nem érvényesül. |
| Az üres felhasználói album kártyája | **NYÍLT** | Ghidra-kör kell: `0x007fc7c0` - a `0x00a6aa00` nem nulla eredménye megszakítja-e a kártyaépítést, és a `0x004ae430` üres taggal mit ad. |
| Azonos dátumú kártyák sorrendje | **NYÍLT** | Ghidra-kör kell: `0x004a7890` - a sorszámlista rendezőkulcsa; és a `0x0049ecd0` összefésülés stabilitása. |
| A virtuális és az albumsor dátumának forrása | **NYÍLT** | Ghidra-kör kell: `0x0055d730` és `0x00452a30` - az új sor dátuma (a `0x004ad220` hívásai); albumsorra a tagságot is tartalmazó katalógus. |
| A `0x007fc4c0` rendezés utáni dátumátalakítása | **NYÍLT** (a kártyasorrendet nem érinti) | Ghidra-kör kell: `0x0098b550` - a `(1, 0, 0, 0)` argumentumok és a két kiolvasott mező jelentése. |

##### Amit kizártam

- **"A kártyadátum a mappa fájlrendszer-ideje"**: cáfolt (a tároló oszlop értéke 86,0%-ban a képek legkorábbi idejével egyezik, nem a mappáéval).
- **"A kártyadátum a mappa legkésőbbi képe"**: cáfolt (a mért 2305 sorból 0 sor egyezik a legkésőbbivel az egyezők között; a minimum 1983).
- **"A qshow a teljes katalógust listázza"**: cáfolt (a `0x004b29d0` állapot-, kategória- és `+0x9d` kapukat alkalmaz, §1-§2; teljes katalógusra csak keresési módban vagy `+0xd8 == 3` esetén emlékeztet, ez utóbbi nincs igazolva).
- **"A `0x00477920` a dátumíró"** (38.2.105): marad cáfolva, az író a `0x004460a0` → `0x006a5c60`.
- **"A `+0x0c == 2` gyűjteménytípus"** (38.2.110 cáfolata megerősítve): az állapot a sor kiértékelt állapota, nem típus; a típust a token és a fájlnév adja (§2 táblázat).

##### Bizonyítottság

**Megerősített:** a getter, az író és a tábla azonossága (két út: utasítás- és konstruktor-olvasat; ugyanaz az oszlopkulcs és tábla); az `autodate` képlete és a `0x0098b650` helyi időre váltása (utasítás és a katalógus-mérés pontosan az 1-2 órás eltolással egyezik); a `category` → `catdata` kapcsolat (a binárisban a `Labels` alapértelmezés és a konstruktor, az adatban hat nevesített egyezés). **Erős:** a sorállapot-gép döntési szabálya (utasításszinten olvasva, a job-239 katalógus kártyahalmaza egyezik); a `catdata` `state` hatása a rekordok kimaradására (két helyen olvasott, felvétel nélkül). **Feltételes:** a `+0x167` és `+0x1d` jelzők jelentése, a `+0xd8` mód, a `0x007fc4c0` utáni átalakítás, a stabilitás az összefésülő lépésben, a virtuális és albumsorok dátuma.

**Módosított fájlok ebben a szakaszban.** Ez a 38.2.190 szakasz és a `picasa-idorend-viselkedes.md` két érintett sora. Kódot, tesztet, eredeti binárist, felvételt vagy mérőadatot nem módosítottam; az ideiglenes mérőszkriptek a munkafa `.bt/` mappájából törölve.

#### 38.2.200 Colab-mérésterv a #6532 látható, nyitott pontjaihoz (#6532, 2026-11-13)

**Hatókör és állapot.** Ez a szakasz mérésterv, nem mérés: új eredeti-Picasa képernyőkép vagy felvétel ebben a körben nem készült, a feladatokat nem adtam fel (a feladást a hívó végzi). A §38.2.127 és a §38.2.160 azon látható pontjait fedi, amelyeket statikusan nem lehet eldönteni: (1) a Space első fotója és a szünetelés, (2) a Ctrl+Space látható hatása, (3) a `Preparing timeline...` betöltésjelző, (4) az Escape utáni szülőnézet-kijelölés. Nyolc feladat-JSON készült a munkafa `.bt/colab-6532/` mappájában (a mappa nem része a repónak; a lépéssorok az alábbi táblázatban teljesen olvashatók, tehát a fájlok újra előállíthatók). Mind a bevált job-239/241/373 vázat követi: `"indulas": "alapallapot"`, `"wine_desktop": true`, `"mintakeszlet": "idorend"`, `"kimenet": ["kepernyokep", "allapot"]`, és három tíz másodperces várakozással indul (a job-241 `allapot.json`-ja szerint a 2-4. kép dhash-e azonos, tehát a könyvtár az első várakozás végére betöltött). A JSON-okat a végrehajtó szabályainak tükrével ellenőriztem (a `v3` mezők, a billentyűminta, `var` > 0 és legfeljebb 10, legfeljebb 40 lépés, a felvételek összege legfeljebb `keret.perc * 60 - 120` mp): mind a nyolc érvényes.

##### 1. Amit a végrehajtó nem enged, és a terv ehhez igazodik

**Cáfoló kísérlet (15.2).** Első célpontom az volt, hogy a betöltésjelző „sűrű képernyőképekkel” mérhető-e, ahogy a feladat kérte. A végrehajtó forrása ezt cáfolja:

- Minden lépés ELŐTT készül egy képernyőkép és egy állapotrekord: az N. kép az (N-1). lépés utáni állapot, az utolsó kép a záró lépés, annak 1,0 s szünete és még 2 másodperc várakozás után készül.
- Minden lépés UTÁN fix 1,0 másodperces szünet van, ez a feladatból nem rövidíthető; a `var` értéke 0-nál nagyobb és legfeljebb 10 másodperc (a `0` érvénytelen).
- Következmény: két kép között legalább kb. 1 másodperc és a kép elkészítésének ideje telik el, és a Ctrl+5 utáni első kép is legalább ennyivel a leütés után készül. A job-373 felvételén a 75. képkocka még a könyvtárnézet, a 76. már a teljes Időrend-panel, köztes képkocka nincs (38.2.85, 15 kép/mp, azaz 67 ms felbontás). Ha a betöltésnek van látható szakasza, az ennél rövidebb, ezért képernyőképpel nem kapható el; az egyetlen eszköz a `felvetel` lépés (15 kép/mp, legfeljebb 180 s). A leütés és a panel megjelenése közti idő így sem mérhető, mert a leütés időpontja nincs a felvételen (38.2.85).
- A „rögtön Escape” a következő lépés, vagyis a Ctrl+5 után legalább 1,0 s + a kép ideje múlva érkezik. A megnyitó átmenet (38.2.85: 1,000 s) KÖZBEN küldött Escape ezzel a végrehajtóval nem kérhető; a 02b feladat a legkorábbi elérhető Escape-et méri, a felvétel megmutatja, hol érkezik az átmenethez képest.

A betöltésjelzőhöz ezért nincs „sűrű képernyőkép” feladat: a 03a felvételre épül. A séma ellenőrzése is megtörtént: a `ctrl+space` megfelel a végrehajtó billentyűmintájának (`ctrl+` módosító és `space`), a `kattint [90, 311]` pedig a 1280×1024-es képernyőn belül van.

##### 2. A nyolc feladat

A „kép N” mindenhol a végrehajtó N. képernyőképe (az N. lépés előtti állapot). A táblázat a három kezdő `var 10` utáni lépéseket adja; a `keret.perc` a harmadik oszlopban.

| Fájl (`6532-<név>.job.json`) | Lépéssor a kezdő várakozások után | Perc | Mit dönt el |
|---|---|---:|---|
| `01a-space-2019-marcius` | `ctrl+5`, 3, `Right`, 2.5, `Right`, 2.5, `space`, 2.5, 3, 4, `space`, 2.5, 3, `space`, 2.5, 4, `Escape`, 2, 2 | 15 | Space első fotója és szünetelése a 7 képes kártyán; a második és a harmadik Space |
| `01b-space-2014-november` | `ctrl+5`, 3, `Right`, 2.5, `space`, 2.5, 4, `Escape`, 2, 2 | 12 | az első fotó a 3 képes kártyán; kijelölés Space+Escape után |
| `01c-space-picasateszt` | `ctrl+5`, 3, négyszer (`Right`, 2.5), `space`, 2.5, 4, `Escape`, 2, 2 | 12 | az első fotó a 24 képes, felismerhető képű gyűjteményen |
| `01d-ctrl-space` | `ctrl+5`, 3, `Right`, 2.5, `ctrl+space`, 2.5, 4, `space`, 2.5, 3, `Escape`, 2, 2 | 12 | a Ctrl+Space látható hatása |
| `02a-visszateres-mappafokusz` | `kattint [90,311]` (2019_marcius), 2, `ctrl+5`, 3, `Right`, 2.5, `Left`, 2.5, `Escape`, 2, 2 | 12 | kijelölés valódi mappafókuszból, Right+Left után |
| `02b-visszateres-azonnali-escape` | `kattint [90,311]`, 2, `felvetel 30`, `ctrl+5`, `Escape`, 2, 2 | 12 | kijelölés a legkorábbi Escape után, felvétellel az időzítéshez |
| `02c-visszateres-album-es-gyujtemeny` | `ctrl+5`, 3, négyszer (`Right`, 2.5), `Escape`, 2, 2, `ctrl+5`, 4, ötször (`Right`, 2.5), `Escape`, 2, 2 | 15 | kijelölés a PicasaTeszt és a Recently Updated kártyáról, fókusz nélkül |
| `03a-betoltesjelzo-felvetel` | `felvetel 100`, 10, 4, háromszor (`ctrl+5`, 5, `Escape`, 3) | 15 | látszik-e a betöltésjelző hideg és ismételt belépéskor |

A `kattint [90, 311]` a bal oldali mappafa `2019_marcius (7)` sora (a job-241 `kepernyo__04.png` és `kepernyo__14.png` képéről: a sorok y értéke `PicasaTeszt` 223, `2021_eltero_fajlido` 267, `2019_marcius` 311, `2014_november` 355, `2009_majus` 399). A kezdő állapot a job-241 `kepernyo__04.png`-jén nincs kijelölt mappa; a `kepernyo__14.png` mutatja, hogyan néz ki a kijelölés: sötét sor a mappafában, kék keretes bélyegkép, a fájlnév az alsó állapotsorban.

##### 3. Pontonként: jóslat a bináris alapján és mi cáfolná

**3.1 Space első fotója és szünetelése (01a, 01b, 01c).**

- *Bináris alap.* A `0x00801270` Space-ága a `[this+0x3bb]` állapotától függően a `0x00801130` váltóhoz vagy a `0x00803110` OneUp-objektumváltóhoz jut (38.2.127 §2); a `0x00803110` nem ad át fotóindexet vagy rekordazonosítót (38.2.160 §2), tehát a kezdőkép nem a qshow hívásparamétere. A job-373 felvételen az első Space szünetelő felületet hozott, az 1/7 kép 15,5 másodpercig pixelre azonos maradt (38.2.150 4. pont); a job-240 3 és 8 másodpercnél azonos képet adott (38.2.82).
- *Jóslat.* A vetítés a kártya gyűjteményének első fotójával indul és szünetel: 01a kép 11-14: `1/7`, `2019-03-08 09:15`, a felirat `Exit Slideshow`, `Timeline`, `Display Time 3 seconds`, a négy kép pixelre azonos; 01b kép 9-11: `1/3`, `2014-11-02 15:30`; 01c kép 15-17: `1/24`. A 01c képazonosságára nincs bináris jóslat (a PicasaTeszt képein nincs beleégetett felirat): a 24 kép könyvtári sorrendjét a job-241 `kepernyo__04.png` adja, ebből látszik, hogy a vetítés a könyvtári sorrend, a dátum vagy a fájlnév szerint indul. Az Escape utáni kép (01b 12-14, 01c 18-20, 01a 21-23): a Space előtti kártya mappája marad kijelölve, egyedi fotókijelölés nélkül (ahogy a job-240: 2019_marcius, 38.2.82).
- *Kiegészítő, bináris jóslat nélkül (01a második és harmadik Space).* A `0x00801130` a `+0x3bb` állapotot váltja, de hogy a OneUp felületen ez lejátszás/szünet váltás-e, nem ismert. Munkahipotézis: a második Space elindítja a lejátszást (a 15. kép még `1/7`, a 16. és a 17. képen a sorszám nagyobb, kb. 3 másodpercenként egy kép), a harmadik megállítja (a 18-20. kép azonos).
- *Cáfolná.* A kép 11 nem `1/7` vagy más gyűjtemény képe; a kép 11-14 között a képterületen bármilyen pixelkülönbség (nem szünetel); `n/3`, `n/24` esetén n ≠ 1; a 15-17. képek azonosak a 11-14.-kel (a Space nem váltja a lejátszást, a hipotézis téves).

**3.2 Ctrl+Space (01d).**

- *Bináris alap.* A Ctrl+Space ág a `[this+0x3ba]` jelzőt 1-re írja (`0x008012fb`), és nem hívja a `0x00801130`-at vagy a `0x00803110`-et (38.2.127 §2). A `0x00800a30` rajzoló a jelzőtől függő ágon a `[this+0x3c4]` képobjektumot a teljes qshow rajzterületre adja a `0x008001c0` rajzolónak (38.2.160 §1).
- *Jóslat.* A Ctrl+Space után a OneUp felület NEM indul (nincs `Exit Slideshow` felirat, a `qshow` marad az ablaklistában), és a qshow-panel (x=340, y=272, 600×480, 38.2.85) tartalma megváltozik az alapképhez (kép 8) képest, a változás a 9-11. képen állandó. A kép tartalma (a `+0x3c4` forrása) nincs meg, ezért a jóslat csak a hatás meglétét és helyét mondja ki, nem a tartalmát.
- *Cáfolná.* A panel pixelre azonos a 8-11. képen (a jelző ebben az állapotban nem rajzol, vagy a billentyű nem jutott el a Picasáig: a Wine/X réteg a Ctrl+Space-t elnyelheti, ezért a null eredmény csak gyenge cáfolat; a kontroll a sima Space a 11. lépésben: ha a 12-14. kép pontosan a 01b 9-11. képével egyezik, az sem bizonyítja a jelző hatását); vagy a OneUp felület megnyílik (a 38.2.127 szerinti külön ág cáfolt).

**3.3 Betöltésjelző (03a).**

- *Bináris alap.* A `0x005e8a70` Időrend-belépő a `Preparing timeline...` szöveggel `ytProgress` objektumot készít; a fogadó (`CThumbUI+0x278`) `+0x14` célja (`0x00566630`) a `Press ESC key on keyboard to abort` szöveget állítja, a `+0x0c` cél (`0x00566320`) a `thumbui/modalprogressfloater` és `thumbui/progressbarfill` elemeket kezeli, de csak `DAT_00d67914 != 0` esetén (38.2.160 §3). Az `idorend` készlet hat kártyát ad (öt mappa és egy album), így a feldolgozó ciklus rövid. A job-373 felvételen a könyvtárnézet és a teljes panel között nincs köztes képkocka, tehát jelző nem látszott (38.2.85).
- *Jóslat.* Mindhárom belépésnél (hideg indítás utáni első, majd két ismételt) az utolsó tiszta könyvtárkép és az első panelkép között vagy nincs köztes képkocka, vagy a köztes képkockán se lebegő ablak, se folyamatjelző sáv, se `Preparing timeline...` vagy `Press ESC key on keyboard to abort` szöveg nem látszik.
- *Cáfolná.* Legalább egy köztes képkocka lebegő ablakkal, folyamatjelző sávval vagy a két szöveg valamelyikével (rögzítendő: a képkockák száma, a jelző helye és mérete, melyik belépésnél látszott).
- *Határ.* A negatív eredmény nem választja szét azt, hogy a `DAT_00d67914` kapu nulla, vagy a betöltés ennél a hat kártyánál túl gyors a jelzőhöz: csak a pozitív eredmény dönt. Az sem mérhető, hogy a könyvtárnézet a leütés után mennyi ideig áll változatlanul a panel megjelenése előtt, mert a leütés időpontja nincs a felvételen.

**3.4 Escape utáni kijelölés (02a, 02b, 02c).**

- *Bináris alap.* Az Escape a `0x007fb820`-on át a `ytWindow` host `0x00983270` callbackjéig jut, ami saját ablakára `WM_CLOSE` üzenetet küld; ez az út nem nevez meg mappát vagy fotót (38.2.127 §4, 38.2.160 §4). A kijelölést tehát a qshow kártyaállapota vagy a könyvtári felület állítja be, a bináris út nem. A qshow a belépéskor a nulladik kártyával indul: `0x008037e0` → `0x008018a0(0)` (38.2.83); a job-241-ben az Escape után kijelölt `2021_eltero_fajlido` mappa ellenére a második Ctrl+5 a 2009-es kártyával nyílt.
- *Mért előzmény.* job-241 (nincs kezdő fókusz, három Right): a 2021-es mappa és első képe kijelölt. job-239 (a `Recently Updated` albumkártyán, Home/End után): a visszatérés a belépés előtti `PicasaTeszt` mappanézet, a kijelölés nem lett olvasva (38.2.81). job-240 (Space, Escape): 2019_marcius maradt kijelölve.
- *Jóslat (02a).* A Ctrl+5 a kattintott 2019_marcius fókusz ellenére a `2009_majus` kártyával nyílik (7-8. kép), a Right a `2014_november`, a Left megint a `2009_majus` kártyára visz (11-12. kép); az Escape után (13-15. kép) a `2009_majus` mappa és első képe (`2009_majus_01.jpg` az állapotsorban) kijelölt, vagyis az Escape pillanatában látott kártya számít, nem a belépési fókusz.
- *Jóslat (02b).* Navigáció nélkül ugyanaz a szabály: a 9. képen a `2009_majus` mappa és első képe kijelölt. A felvétel megmutatja, a Ctrl+5 leütéséhez képest mikor tűnik el a qshow.
- *Jóslat (02c).* A PicasaTeszt kártya után (kép 14, Escape: 15-17): a `PicasaTeszt` mappa és első képe kijelölt. A `Recently Updated` albumkártya után (kép 29, Escape: 30-32) bináris jóslat nincs, mert az album nem mappa: két lehetőség van, vagy a `Recently Updated` sor jelölődik ki az Albums alatt, vagy a mappafában nincs sötét sor (a job-239 a belépés előtti nézetet mutatta). A második belépés nyitókártyája (kép 19) a jóslat szerint újra `2009_majus`.
- *Cáfolná.* 02a: a `2019_marcius` marad kijelölve (a belépési fókusz tér vissza), vagy a qshow nem nyílik meg (a 7-8. képen nincs `qshow` az ablaklistában; ekkor a Right és a Left a könyvtárban mozgat, és a feladat a „mappafókusz gátolja a belépést” kérdést dönti el; a job-241 második belépése 2021-es fókusszal megnyílt, a job-240 második belépése a OneUp utáni 2019-es fókusszal nem). 02b: a kijelölés eltér a 02a-étól (a közbeni navigáció számít). 02c: a PicasaTeszt kártya után más mappa jelölődik ki.

##### 4. Olvasási rend (a kiértékeléshez)

- **Kijelölés** a képernyőképen: (a) sötét sor a bal oldali mappafában, (b) kék keretes bélyegkép, (c) az alsó állapotsor fájlneve (minta: job-241 `kepernyo__14.png`).
- **Szünetel-e:** a OneUp-képterület `ImageChops.difference(a, b).getbbox()` értéke a 01a 11-14., a 01b 9-11., a 01c 15-17. képek között; `None` = pixelre azonos.
- **Ctrl+Space:** a qshow-panel (340, 272, 600×480) vágásának különbsége a 01d 8. és 9-11. képe között; a `qshow` jelenléte az `allapot.json` ablaklistájában.
- **Videó (03a, 02b):** felbontás képkockákra, másodpercenként 15 képpel; a Ctrl+5 leütését a felvétel nem rögzíti (38.2.85), ezért a belépés pillanata az utolsó tiszta könyvtárkép és az első panelkép. A keresés a TELJES képre vonatkozik, mert a lebegő folyamatjelző a főablakban lenne, nem a 600×480-as panelben; a köztes képkockákat az előző könyvtárképhez kell hasonlítani a panelen kívüli területen.
- A feladat jelentésében rögzítendő a végrehajtó tényleges futásideje és a képek sorszámozása; az első képek időzítése lépésenként kb. 1 másodperc és a kép elkészítési ideje, tehát a „kb. N másodperc” állítások ±0,5 másodperc pontosságúak.

##### 5. Bizonyíték- és nyitottkérdés-tábla

| Állítás | Forrás | Fok |
|---|---|---|
| A végrehajtó a lépések előtt készít képet, minden lépés után 1,0 s szünetet tart, `var` > 0. | a végrehajtó forrása (`picasa-colab-jobs` figyelő, lépésciklus és `var`-ellenőrzés) | olvasott kód, nem futtatott mérés |
| A job-373 felvételén a könyvtárnézet és a panel között nincs köztes képkocka (75. könyvtár, 76. panel), jelző nem látszott. | mérés (job-373, 38.2.85) | korábbi mérés |
| A Space a `0x00803110` útján indexet nem ad át; a kezdőkép nem a qshow paramétere. | bináris (38.2.160 §2) | megerősített az utasításolvasatban |
| A Ctrl+Space a `+0x3ba` jelzőt írja, a rajzoló a `+0x3c4` képet a teljes rajzterületre adja. | bináris (38.2.160 §1, két független út) | megerősített; a kép tartalma NINCS MEG |
| A `DAT_00d67914` kapu feltételesíti a lebegő ablakot és a folyamatjelző sávot. | bináris (38.2.160 §3) | feltételes a láthatóságra |
| Az Escape után az utolsó látott kártya mappája és első képe kijelölt (job-241). | mérés (38.2.83) | feltételes, egy futás |
| A 3.1-3.4 pontok jóslatai a fenti források következményei, nem mérések. | ez a szakasz | **jóslat, mérés nincs** |

**A két független út.** Itt a „két út” a jóslat forrására értendő: A út a binárisból olvasott kapuk és kezelők (38.2.127, 38.2.160), B út a korábbi felvételek (job-239, 240, 241, 373). A Ctrl+Space és a betöltésjelző jóslata a bináris A útra épül, a Space-é és a visszatérésé a B útra; mindhárom pont kapja a másik utat kontrollnak a feladatokban (01b-01c a job-240/373 ellen, 02a-02c a job-241 ellen, 03a a job-373 ellen). A második út független megerősítését a mérés adja, nem ez a szakasz.

**Nem tervezett, és miért.**

- *Üres katalógusbeli belépés (`IDS_MUST_SELECT`).* Az `idorend` készlettel a katalógus sosem üres; a job-241 `kepernyo__01.png` üres könyvtára („No photos found”) a betöltés közbeni pillanat, így egy ott küldött Ctrl+5 eredménye nem determinisztikus, és a lépések közti 1,0 s miatt időzítve sem kérhető.
- *A Space által átadott rekord bináris azonosítása.* A mérés csak a látható eredményt adja (melyik kép jelenik meg); a `0x00803110` rekordátadása Ghidra-kör marad ([blokkoló], 38.2.160 §6).
- *Escape a megnyitó átmenet közben.* A végrehajtó rése miatt nem kérhető (1. rész).

**Következő irány megnevezve.** (1) A hívó feladja a nyolc feladatot; javasolt sorrend a döntési értékük szerint: `02a`, `01a`, `03a`, `02c`, `01d`, `01b`, `01c`, `02b` (a végrehajtó egyszerre egyet futtat, a legkisebb jegyszám előbb). (2) Ha a `03a` negatív, a maradék statikusan dönthető: a `DAT_00d67914` íróinak és olvasóinak teljes `.text`-pásztázása (a `paszta.py` memóriakapuval, minden regiszterbázissal); ha az Időrend-belépéskor az érték mindig nulla, a lebegő ablak ebben a kiadásban sosem rajzolódik, és a PicasaPy-nak nem kell betöltésjelző. (3) A mérés után a 38.2.160 szerinti 12 nyitott A pont számát a megfelelő pontokkal kell frissíteni; ez a szakasz a pontszámot nem változtatja.

Nyitott kérdések: 4 nyílt · 0 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”

| Kérdés | Állapot | Mi kell hozzá |
|---|---|---|
| A Space első fotója és szünetelése az Időrendből | **NYÍLT**, terv kész | a `01a`-`01c` feladás és kiértékelés (3.1) |
| A Ctrl+Space látható hatása | **NYÍLT**, terv kész | a `01d` feladás és kiértékelés (3.2) |
| A betöltésjelző látható megjelenése | **NYÍLT**, terv kész | a `03a`; negatív eredménynél a `DAT_00d67914` írói (3.3) |
| Az Escape utáni kijelölés általános szabálya | **NYÍLT**, terv kész | a `02a`-`02c` feladás és kiértékelés (3.4) |

#### 38.2.170 A kártyaképen látható egymásra tolt, elforgatott lapok forrása és elrendezése (#6532, 2026-11-13)

**Kérdés és eredmény.** Hogyan épül fel az Időrend gyűjtemény-kártyáin látható, egymásra tolt és elforgatott fotólapok kötege az eredeti Picasában, és mi a `0x004ae430 -> 0x00423300 -> 0x00448fb0 -> 0x004114e0` hívási lánc szerepe?
A vizsgálat lezárta a kérdést:
1. **Lapok száma:** legfeljebb **4 lap** (`min(4, elemszám)`, bináris cím: `0x004237ab`, `0x004237b6`).
2. **Elforgatás:** a legfelső kártya (`index == 0`) **egyenes** (forgatási szög: `0.0°`); a mögötte lévő kártyák (`index > 0`) egyenletes eloszlású véletlen forgatást kapnak a **`[-5.73°, +5.73°]`** tartományban (`theta = (rand / 32768.0 - 0.5) * 0.2` radián; `0x00cf4748` = `0.2` double, `0x00c29d20` cos, `0x00c285f0` sin).
3. **Eltolás:** a legfelső kártya eltolása `(0, 0)`; a mögötte lévő kártyák pixelben meghatározott eltolást kapnak: vízszintesen **`dx = 4.0 * index * (2.0 * rand1 / 32768.0 - 1.0)`** képpont (`[-4 * index, +4 * index]` px, konstans: `0x00c7d9d0` = `2.0` double), függőlegesen felfelé **`dy = -index * (4.0 * (rand2 / 32768.0) + 5.0)`** képpont (`-index * [5.0 .. 9.0]` px felfelé, konstansok: `0x00cf3b80` = `-2.0` double, `0x00c7d9d0` = `2.0` double).
4. **Véletlenség és seed:** az elforgatás és eltolás véletlenszerű, az MSVC CRT `_rand()` (`0x00c08221`) függvényét hívja. Ugyanakkor a kötegkép előállítása előtt a `_srand()` (`0x00c08214`) inicializálja az állapotot a gyűjtemény azonosítójából származtatott seeddel: **`param_3 ^ 0x133475`** (`0x00423a2a`, `0x00423a6c`). Ezért egy adott gyűjtemény kártyaképe determinisztikus és stabil az újranyitások során.
5. **Architektúra és hívási lánc:** az eredetiben a köteg nem a 3D nézetben külön rétegekből áll, hanem a `CThumbDB` képfeldolgozója (`0x00423780`) egyetlen, szoftveresen egymásra rajzolt 2D bélyegképet állít elő az affin transzformációs blitterrel (`0x009e6df0`), amit a `0x004115c0` eltárol a gyorsítótárban (`+0x2428`). A `0x004ae430` a `CAlbumState` oldaláról kéri le a bélyegképet a `CThumbDB::vftable` (`0x00c81f78`) `+0x20` slotján (`0x00423300`) át; ha a kép már a gyorsítótárban van, a `0x00448fb0` és `0x004114e0` ág azonnal visszaadja azt. A 3D Időrend (`0x007fc7c0`) ezt az egyetlen kész képet rajzolja textúraként a kártyára.

**A vizsgálat két független útja.**
- *A út (utasításszintű gépi kód):* A helyi `Picasa3.exe` `.text` szekciójának diszasszemblálása (`annot_disasm.py`, Capstone). A `0x00423780` belépési kapuja a `0x004237ab` (`cmp eax, 4`), `0x004237b6` (`mov dword ptr [esp+0x1c], 4`), `0x004237c0` (`mov [esp+0x1c], eax`) utasításokkal rögzíti a legfeljebb 4 lapos határt. A `0x00423a2a` (`xor eax, 0x133475`) és `0x00423a6c` (`call 0x00c08214`) az `_srand` determinisztikus magját adja. A forgatási és eltolási FPU kód a `0x00423ba6`-`0x00423d48` tartományban közvetlenül hivatkozza a `.rdata` lebegőpontos konstansait: `0x00cf4748` (`0.2` double), `0x00c7d9d0` (`2.0` double), `0x00cf3b80` (`-2.0` double), `0x00c7e328` (`1.0` double), `0x00c72150` (`0.5` double).
- *B út (dekompiláció és RTTI / xref architektúra):* A meglévő `2026-10-22-ghidra-sor-247-251.txt` és `2026-10-17-qshow-diavetites.txt` elemzése. Az SQLite index RTTI táblája megerősíti a `CThumbDB::vftable` (`0x00c81f78`) `+0x20` slotjának (`0x00423300`) hovatartozását. A `0x004ae430` a `[esi+0xc4]` pointeren át a `+0x20` slotot hívja (`0x004ae481`). A `0x00423300` a `0x00448fb0` gyorsítótár-lekérdezés (`0x00423326`) és a `0x004114e0` visszatérés (`0x0042333b`) mellett hiány esetén a `0x00423500` hívásán át (`0x004234de`) indítja a `0x00423780` generátort (`0x004236ef`), amely a `0x004115c0` gyorsítótár-íróval menti az eredményt. A Ghidra AST kétmenetes kompozitálást mutat: az első menet a befoglaló téglalapot és a méretet számolja ki (`0x00a4a520`), a második menet az affin mátrixokkal rajzolja a lapokat (`0x009e6df0`).

**Cáfoló kísérlet.**
Azt a feltevést vizsgáltam, hogy a köteg lapjait nem a bélyegkép-kompozitáló állítja össze, hanem az Időrend (qshow) 3D jelenete rajzolja ki laponként külön-külön a `0x008014d0` hívásában, mivel ott is található `_rand()` (`0x00c08221`).
*Cáfolat eredménye:* A `0x008014d0` nem egy kártyán belüli fotóköteget készít, hanem a teljes idősáv gyűjteményeit rendezi el a 3D virtuális térben a pályagörbe mentén. A `0x007fc7c0` (qshow kártyaépítő) a `0x004ae430` meghívásával egyetlen leírót és egyetlen képet rendel minden egyes gyűjteményhez. A `0x00423780` ezzel szemben a `param_4` felületre rendereli rá a lapokat a `0x009e6df0` 2D szoftveres blitterrel. A feltételezés megdőlt: a kártyán látható köteg a bélyegkép szintjén egyesített 2D bitmap, nem pedig futásidejű több kártyás 3D objektumhalmaz.

**Összevetés a PicasaPy implementációjával.**

| Tulajdonság | Eredeti Picasa | PicasaPy jelenleg | Teendő |
|---|---|---|---|
| Lapok maximális száma | Legfeljebb 4 lap (`min(4, count)`, `0x004237ab`, `0x004237b6`). | Legfeljebb 4 lap (`TimelinePanel.qml:242`: `Math.min(4, photos.length)`). | Megegyezik, teendőt nem igényel. |
| Legfelső lap forgatása | Nincs elforgatva (`0.0°`, `0x00423ba6` feltétel átugorja). | El van forgatva (`TimelinePanel.qml:260`: `rotation: index % 2 === 0 ? -7 : 5` -> index 0 esetén `-7°`). | Javítandó: az index 0 kártya forgatása legyen 0°. |
| Mögöttes lapok forgatása | Egyenletes véletlen szög `[-5.73°, +5.73°]` között (`[-0.1, +0.1]` rad, `0x00cf4748` = `0.2` double). | Fix, determinisztikusan váltakozó `-7°` és `+5°`. | Javítandó: a seedelt véletlenszám-generátorból számított `[-5.73°, +5.73°]` tartományú szög. |
| Lapok eltolása | Vízszintesen: `[-4*i, +4*i]` pixel (`0x00c7d9d0` = `2.0`). Függőlegesen: `-i * [5.0 .. 9.0]` pixel felfelé (`0x00cf3b80` = `-2.0`). | Relatív arányszám: `(next_random() - 0.5) * 0.15 * width/height` (`timeline_motion.py:100-131`, `TimelinePanel.qml:257-258`). | Javítandó: relatív arány helyett pixelalapú eltolás, és a hátsó lapok aszimmetrikus felfelé tolása (negatív Y). |
| Véletlenszám mag (seed) | `param_3 ^ 0x133475` (`0x00423a2a`), MSVC CRT `_rand()` / `_srand()`. | Saját, indexből magozott `xorshift` generátor (`timeline_motion.py:113-129`). | Igény szerint közelíthető az eredeti MSVC LCG-hez és a `collection_id ^ 0x133475` seedhez. |
| Renderelési architektúra | 2D szoftveres kompozitálás egyetlen bélyegkép-bitmapbe (`0x00423780` + `0x009e6df0`). | Különálló QML `Item` rétegek a `TimelinePanel.qml` `Repeater`-ében. | A QML rétegzés megtartható, amennyiben a vizuális elrendezés (lapok száma, forgatás, pixel eltolás) megegyezik a binárisból feltárt értékekkel. |

**Bizonyítottsági fok.**
**Megerősített.** Két független forrás (célzott utasításszintű x86 FPU diszasszemblálás a nyers konstansokkal, illetve Ghidra C-dekompiláció és SQLite RTTI/vtábla kapcsolat) egyezik a lapok számában (`min(4, n)`), a forgatási tartományban (`0.2 rad`), az eltolási képletekben (`dx`, `dy`), a determinisztikus magképzésben (`0x133475`) és a hívási láncban.

**Nyitott kérdések a témában.**
Nincs nyitott pont a kártyaképen látható köteg elrendezésére és hívási láncára vonatkozóan. Minden vizsgált kérdés pontos bináris címmel és konstans értékkel igazolt.

#### 38.2.210 A #6532 hat Ghidra-kérdésének lezárása: szupercsoport-jelző, nézetmód, üres album, azonos dátum, sordátum, rendezés utáni átalakítás (#6532, 2026-11-14)

**Hatókör és módszer.** A 38.2.190 végén felsorolt hat kérdés. **A út:** a friss Ghidra-kimenet (`picasapy-agent/referencia/ghidra/2026-11-13-6845-6532-colab-decomp-2.txt`: `0x004a4710`, `0x005d9cc0`, `0x007fc7c0`, `0x00a6aa00`, `0x004a7890`, `0x0049ecd0`, `0x0055d730`, `0x00452a30`, `0x0098b550`), az előző kimenet (`...-6532-colab-decomp.txt`: `0x004b8ee0`, `0x004b29d0`) és utasításszintű olvasat (`picasa_dis.py`, capstone). **B út:** hívók és adat (az index xref-táblája; a db3 `repository.dat`, `catdata`, `albumdata` a PicasaPy `pmpimport` olvasóival), négy teljes `.text` pásztázás a `paszta.py` memóriakapujával (2 884 879 utasítás, mért csúcs-RSS 41,7 MiB: a `+0x2b28`, `+0xd8`, `+0xe0/+0xe4` operandusok; az `0xa09d` és a `0xd67678` cím; a `[x+0x48]` objektum 3. virtuális rése), és hét mérés az eredeti gépi kódon `qemu-i386` alatt (a privát repó `qemu_harness/hb.py` helyi másolata, `timeout 60`, a CRT-allokátor és az inicializáló helyettesítve). Becsült értéket nem használtam. A mérőszkriptek a munkafa `.bt/` mappájában készültek, a szakasz végén törölve.

| # | Kérdés | Válasz | A út | B út | Fok |
|---|---|---|---|---|---|
| 1 | `0x004a4710`: a `+0x1d` jelző forrása | a **szupercsoport kibontottsága**: a `Név~Alnév` alakú kategórianév `~` előtti részéhez tartozó `super:<név>` kulcs szerepel-e a `repository.dat` térképben; szupercsoport nélküli kategóriánál mindig 1 | dekompiláció + `0x004b2e10` hívási környezet | `repository.dat` három katalógusból; az író- és kapcsolófüggvények | **erős** |
| 2 | `0x005d9cc0`: a `+0xd8` nézetmód | 0 dátum, 1 legutóbbi változtatás, 2 név, 3 (nincs menüparancsa) kategóriarejtés nélküli lista, 4 (csak a rendszerleíró adatbázisból), 5 méret; `0xa0cf` megfordít | a hat hívóhely argumentumai | menü- és olvasóoldal, `.text`-pásztázás | **megerősített** |
| 3 | `0x007fc7c0` / `0x00a6aa00`: az üres felhasználói album | nem kap kártyát; a kártyaépítés a hibánál **megszakad**, a hívó eldobja a hibakódot | dekompiláció + utasításszint | QEMU (`0x00a6aa00`) + hibakód-lánc | **erős** (futásidejű felvétel nincs) |
| 4 | `0x004a7890` / `0x0049ecd0`: azonos dátumú kártyák | az összefésülés **stabil**; azonos dátumnál a `0x004a7890` sorrendje marad: kategória, típus, majd név | dekompiláció + oszlopazonosítás | QEMU: 265 rendezés + 44 névpár | **megerősített** (stabilitás), **erős** (kulcssorrend) |
| 5 | `0x0055d730` / `0x00452a30`: sordátum forrása | **egyik sem dátumforrás** (sztring-értékadó, illetve kategória-keresés/létrehozás); a forrás nyitott | dekompiláció + hívási kép | `albumdata` dátumai | a negatív **megerősített**; a forrás **NYÍLT** |
| 6 | `0x0098b550`: rendezés utáni átalakítás | hónap első napjára kerekítés (`COleDateTime(év, hónap, 1, 0, 0, 0)`), és a `[this+0x90]` (az "A tömb") előállítása | utasításszint | QEMU: a valódi `0x007fc4c0` 6 forgatókönyvön, a `0x0098b550` 33 bemeneten | **megerősített** |

##### §1 A `+0x1d` jelző (`0x004a4710`)

1. **A függvény.** `0x004a4710` (324 bájt, `ret 4`): `EAX` a `CAlbumState`, a verem első eleme a kulcs (`char*`, 0 = üres). A táblát így választja: `[+0xe4]`, ha nem nulla; különben `[+0xe0]`; különben `[[+0xc4]+0x2b28]` (`0x004a4716`-`0x004a472a`, `0x004a47a2`-`0x004a47a8`). Zárat tart (a tábla vtáblájának `+0x18`/`+0x1c` rése, vagy `EnterCriticalSection`), majd a `0x004143c0`-t hívja.
2. **A keresés** (`0x004143c0`, 153 bájt): `EDX` a kulcs, a verem a tábla. A kulcsból `CString` lesz (`0x00985ff0`), a kivonatot a `0x00409df0` adja a tábla `+0x60` méretére, a lánc a `[tábla+0x68]` vödrökben van, az összehasonlítás a `0x006f9890` a csomópont `+4` mezőjén. Találatnál az érték (`[csomópont+8]`) nem üres sztring kell legyen: `[érték] & 0xffffff00 != 0` és `[érték+4] != 0` (`0x00414442`-`0x00414455`). Az eredmény igaz, ha van ilyen bejegyzés.
3. **Polaritás.** A perzisztens táblánál a jelző a találat (`0x004a47fc`-`0x004a4800`: `bl = al`); a felülbíráló táblánál a **hiány** (`0x004a4771`-`0x004a4773`: `test al, al; sete bl`).
4. **A felülbíráló táblák** (`+0xe0`, `+0xe4`) a `0x004a4c80`-nal jönnek létre (0x70 bájtos üres tábla, konstruktor `0x00414100`) és szűnnek meg; hívója a `0x00662b20` (a keresés kezelője: `Search results for "%s"`, ez írja a `+0x162` jelzőt, 38.2.190 §2) és a `0x0067be30`. A konstruktor nullázza őket (`0x004a17ac`, `0x004a17b2`). Keresésen és ezen a másik módon kívül tehát a perzisztens tábla dönt.
5. **A perzisztens tábla a `CThumbDB+0x2b28`**: a db3 `repository.dat` tartalma. Más kulcsait is ide írják: `DBID` (`0x004199d0`), `IDPersist`, `KeywordVersion` (`0x0041c340`), `rawversion`, `colorspaceversion`, `gpsversion` (`0x0041ee10`), `frversion`, `contactsversion` (`0x00488880`).
6. **A hívó** a `0x004b2e10` (kategóriaváltáskor futó fejlécépítő; hívási hely `0x004b2f7d`): a kategórianevet a `0x004b0880` a `~`-nél bontja (`_strchr(név, 0x7e)`, `0x004b08ba`-`0x004b08bd`): az előtag a szupercsoport, az utótag az alnév. Ha az új szupercsoport neve azonos az előzővel, a jelző marad (`0x004b2ef8`-`0x004b2f11` → `0x004b3211`). Ha nincs szupercsoport: `+0x1c = 0`, `+0x1d = 1` (`0x004b31fd`-`0x004b3201`). Egyébként a kulcs `"super:" + szupercsoport-név` (`0x004b2f2a`-`0x004b2f4c`, sztring `0x00c832d0`); keresési módban (`CAlbumState+0x162` nem nulla) `+0x1d = 1` (`0x004b2f59`-`0x004b2f62`), különben `+0x1d = 0x004a4710(kulcs)` (`0x004b2f6d`-`0x004b2f82`).
7. **A hatás** (`0x004b3440`-`0x004b3469`): a környezetrekord `+0x00` mezője -1 (látható), ha a kategória "látszik" (a `catdata` `state` nem nulla, vagy keresés van, 38.2.190 §2) **és** `+0x1d` nem nulla; különben a kategória azonosítója. A `0x004b29d0` a sort kihagyja, ha a kategóriája egyenlő ezzel a mezővel (`*piVar3 == iVar2` → `return 0`). A `+0xd8 == 3` módban a `0x004b2e10` nem is fut (`0x004b2a2c`), tehát a rejtés nem érvényesül (§2).
8. **Az írók** (kibontás és összecsukás): `0x004a4860` (557 bájt) a kulcsot `"1"` (`0x00c81288`) vagy üres értékre állítja a `0x004141d0`-nel (`0x004a48f3`); `0x004a4a90` váltja; a `"super:"` kulcsot a `0x004abba0` állítja össze (`0x004abbcc`), a fejlécrekord sorszáma szerinti kibontást a `0x004ab9a0` végzi (5-ös, 6-os, 7-es típusú fejlécrekord; 1 kibont, -1 vált). A hívók a parancskezelők: `0x005cb990` (`0x005cc252`, `0x005cc25f`), `0x005d3290`, `0x005f9ce0`.

**B út: a három katalógus `repository.dat` fájlja.** A fájl kulcs-érték párokból áll (a kulcs után a `1` vagy a verziószöveg).

| katalógus | `super:` kulcsok | a `catdata` nevei, amelyekben van `~` | következtetés |
|---|---|---|---|
| tulajdonos (`Picasa2`, 140 bájt) | nincs | `Downloaded Albums~sipos.aniko13`, `Downloaded Albums~krisztuka76`, `Downloaded Albums~103651636470512534794` | a `Downloaded Albums` szupercsoport lecsukott, e három kategória sorai nem kártyák |
| `Picasa2-arcok` (1386 bájt) | `super:golden-kit3` | `golden-kit3~export`, `golden-kit-fix~export`, `golden-kit~export`, `PicasaPy-merokit~export` | csak a `golden-kit3` kibontott; a másik három szupercsoport lecsukott |
| `1557-masolat-mentese` (1386 bájt) | `super:golden-kit3` | ugyanaz a négy | ugyanaz |

A kulcs (`super:golden-kit3`) pontosan a kulcsképzés szerinti alak a `golden-kit3~export` kategóriára. A térkép ugyanitt tárolja a fanézet kibontott csomópontjait (fordított perjelre végződő útvonalak, érték `1`), valamint a `flat`, `all`, `Folders`, `Mappák` kulcsokat; ezek jelentését nem vizsgáltam. **Amit az adat nem bizonyít:** a polaritást (találat = kibontott) csak a kód mondja ki, élő felvétel nincs; a kibontás parancsok (`1` = kibont) és a lekérdezés együtt adják az irányt.

##### §2 A `+0xd8` nézetmód (`0x005d9cc0`, `0x004b07c0`)

**A beállító** a `0x004b07c0` (75 bájt, `ret 4`): a verem a `CAlbumState`, `EDX` a mód, `CL` a megfordítás. Azonos mód és megfordítás esetén `0x000f4242`-t ad; különben beírja a `+0xd8`, `+0x165` mezőt (`0x004b07dc`-`0x004b07e2`), és a `0x006dc4c0(…, 1)` hívással újraépíti a listát (`0x004b0803`). A `0x005d9cc0` két hívása a szöveges parancsoké (`thumbui/namesort` → `EDX = 2`, `0x005db20c`; `thumbui/datesort` → `EDX = 0`, `0x005db26f`); a menüparancsok a `0x005cb990` kapcsolójából a `0x005d30f0`-n át érik el (hat hívás: `0x005cbbfa`, `0x005cbc17`, `0x005cbc34`, `0x005cc70a`, `0x005cd5f9`, `0x005cd61e`; a `0x005d30f0` hívása `0x004b07c0`-ra: `0x005d3127`). A parancsazonosítókat a `0x005cb990` három ugrótáblájából (`0x005cd9fc`, `0x005cdc30`, `0x005cdefc`) olvastam ki.

| `+0xd8` | beállító | az összehasonlító (`0x004a7890`) |
|---|---|---|
| 0 | `thumbui/datesort`; `0x9c8b` `ID_VIEWBYDATE` (`0x005cbbea`) | a `date` oszlop double értéke, csökkenő (az újabb előbb) |
| 1 | `0x9cbd` `ID_VIEWBYRECENT` (`0x005cbc21`) | a `0x004ae0d0` double értéke, csökkenő |
| 2 | `thumbui/namesort`; `0x9c8c` `ID_VIEWBYNAME` (`0x005cbc04`) | nincs külön ág: a név ága |
| 3 | `0xa09d` (`0x005cd5e6`) | nincs külön ág (név); a `0x004b29d0` nem hívja a `0x004b2e10`-et, tehát nincs kategória- és szupercsoport-rejtés |
| 4 | nincs parancs; csak a `Preferences\datesort` rendszerleíró értékből (`0x004a195f`-`0x004a1991`, mentés `0x004a3790`) | a `0x004502e0` double értéke, csökkenő |
| 5 | `0x9dc8` `ID_VIEWBYSIZE` (`0x005cc6f7`) | 64 bites bájtösszeg (`0x004507e0`), csökkenő |
| (fordítás) | `0xa0cf` `ID_VIEWREVERSE` (`0x005cd603`: ugyanaz a mód, `+0x165` ellentettje) | az eredmény előjelét váltja |

Az irány: a rendező hívás `(a = második elem, b = első elem)`, negatív eredmény = a előbb; az összefésülő `>= 0` esetén az első marad elöl (`0x004bab56`, `0x004bb071`). Ezért `a < b` esetén a pozitív `+1` csökkenő sorrendet ad.

**B út.** A menüoldal (a spec `picasa-menu-parancsok-viselkedes.md` 36.3-36.5 és `picasa-konyvtar-eszkoztar-viselkedes.md` 4/b pontja, a pipázó `0x00574b70`) ugyanazt a 0, 1, 2, 5 négyest és a `0xa0cf` megfordítást adja; a 3 és a 4 az olvasók oldaláról jön (`0x004a7890`, `0x004b29d0`). A `0xa09d` azonosító közvetlen operandusként a teljes `.text`-ben **sehol** nincs (0 találat), a menüépítő `0x00559150` nem tartalmazza, és a `.rsrc`-ben nincs menü, ezért a parancs neve és forrása nincs meg. Ez nem blokkoló: a 3-as mód a felhasználónak ismert menüből nem érhető el.

**Az Időrend szempontjából:** a kártyalista a nézetmódtól függetlenül dátum szerint újrarendeződik (§4, §6), tehát a mód csak az azonos dátumú kártyák sorrendjére és a 3-as mód rejtésmentességére hat.

##### §3 Az üres felhasználói album kártyája (`0x007fc7c0`, `0x00a6aa00`)

1. **A ciklus** (`0x007fc7c0`, kártyánként, rendezett sorrendben): `0x004ae430(sor, &rekord)` (a rekordot előtte nullázza: `rekord+8` szélesség, `rekord+0xc` magasság `0`), `0x007fa5b0` a kártya konstruktora, majd `0x00a6aa00(…, -1, -1, -1, -1)` másolja a rekord képét a kártyába (`0x007fcca7`). A `0x004ae430` visszatérési értékét a ciklus **eldobja**.
2. **A `0x00a6aa00`**: a forrás (`EAX` = a rekord) szélessége és magassága is nagyobb kell legyen nullánál, különben `4`-gyel tér vissza. **Nem nulla eredménynél a `0x007fc7c0` megszakad** (`0x007fccae`-`0x007fccb0` → `0x007fcf7a`): a hibakóddal visszatér, a már felvett kártyák a `+0xb0` listában maradnak, a hátralévőket nem építi, és a fókuszeltolás számítása (`[this+0x20] = [this+8] - sorszám * [this+0x30]`) **kimarad**.
3. **A hívó** (`0x008037e0`, `0x008039c5`) a `0x007fc7c0` visszatérési értékét **nem vizsgálja**: a következő utasítás `mov eax, esi` és a `0x007fb210` hívása. Tehát a qshow hibajelzés nélkül, csonka kártyalistával és be nem állított fókuszeltolással indul.
4. **Mi kap képet** (`0x00423300`, `CThumbDB` `+0x20`): a gyorsítótár találata (`0x00448fb0`) kész képet ad; a `0x00448a10` a sor tokenjét a `CThumbDB+0x2e98` sztringjével hasonlítja, és ha igaz értéket ad, a `0x00423300` `0`-val tér vissza kép nélkül (a feltétel jelentését nem bontottam tovább); nem üres tagság esetén a kártyakép készül (`0x00423500`); **nulla tag esetén `3` a visszatérési érték és a rekord üres marad** (`uVar1 >> 1 == 0` → `return 3`). Mindkét kép nélküli út a `0x00a6aa00`-nál `4`-et ad.
5. **Következmény.** Az üres felhasználói album sora (2-es állapotú, 38.2.190 §2) nem lesz kártya. A kártyák **növekvő dátum szerint** épülnek (§6), tehát a megszakadás a hibás sor dátumától kezdve minden **későbbi** kártyát elveszít; egy dátum nélküli (949998,0) sor a sor végén van, ezért ott semmi nem vész el, csak a fókuszeltolás marad ki.

**B út (QEMU).** A valódi `0x00a6aa00` négy bemenetre (szélesség, magasság: `0,0`; `0,5`; `5,0`; `-1,5`) mind a négyszer `4`-et adott. A hibakód-láncot (`0x00423300` → `3`, `0x004ae430` továbbadja, `0x007fc7c0` eldobja, `0x00a6aa00` → `4`, megszakadás, `0x008037e0` eldobja) utasításszinten olvastam végig. **Adat:** a tulajdonos katalógusában 17 felhasználói album van (üres `filename`, `]album:` token, `Labels` kategória), valós dátummal (40 180,73 és 40 950,79 között); a tagságuk a db3-ban nem olvasható, ezért nem eldönthető, van-e köztük üres. Futásidejű felvétel üres albummal nincs.

##### §4 Azonos dátumú kártyák sorrendje (`0x004a7890`, `0x0049ecd0`)

1. **Az összefésülés stabil** (A út). A `0x0049ecd0` `fld` + `fcomp` + `test ah, 0x41`: a jobb elem csak akkor megy előre, ha a bal **szigorúan nagyobb** (`0x0049ecf2`-`0x0049ecff`); egyenlőségnél a bal marad. A `0x0049cd60` első menetei ugyanígy cserélnek csak szigorú nagyobbnál (`0x0049ce0b`-`0x0049ce19`, `0x0049ce5c`-`0x0049ce6d`). A rendezés **növekvő** a `double` kulcson.
2. **Mérés (B út, QEMU).** Az eredeti `0x0049cd60`-t 265 forgatókönyvön futtattam (n = 2-től 32-ig, sok ismétlődő kulccsal; a CRT-allokátor helyettesítve): **mind rendezett, permutáció és stabil** (egyezés a Python stabil rendezésével). Köztük a kártyadátumhoz hasonló vegyes kulcsok (`46296,0`, `45748,0`, `949998,0` többszörösen) is.
3. **Mi adja a bemeneti sorrendet.** A `0x007fc7c0` a `+0x158` rekordlistából veszi a sorokat; ezt a `0x004b8ee0` állítja elő a `+0x148` sorszámlistából, amelyet a `0x004baaa0` (ugyanaz az alulról felépülő összefésülés; a hívó a `>= 0` esetben az elsőt tartja elöl: `0x004bab56`, `0x004bb071`) rendez a `0x004a7890` összehasonlítóval. Az összehasonlító oszlopai a `0x004a6dc0` betöltőből: `D+4` `CThumbDB+0x8c8`, `D+8` `+0x928`, `D+0xc` `+0xb50` (`albumdata name`), `D+0x10` `+0xbb0` (`filename`), `D+0x14` `+0xaf0` (`token`), `D+0x18` `+0xc10` (`date`), `D+0x1c` `+0xc78` (`category`); `D` a `0x00d67678` globális, amelyet a `0x004b8ee0` a rendezés idejére állít be (`0x004b9150`-`0x004b9176`); ha a három oszlop-gyorsítótár nem fedi az összes sort, `D` nulla marad, és az összehasonlító a `0x00453da0` név-útjára esik (ezt nem vizsgáltam).
4. **A kulcssorrend** (a = második, b = első elem; a negatív eredmény a-t előre teszi):
   1. a `D+8` oszlop bájtértéke a kategória sorszámán át, **csökkenő** (a `catdata` `catpri` oszlopa, 0 és 100 közötti értékekkel; az oszlop nevét a betöltő nem mondja ki: feltételes);
   2. a kategória neve (`D+4`, `0x004a71e0`), kisbetűsített ASCII-összehasonlítással, növekvő;
   3. ha **mindkét** sor `filename` oszlopa üres (album vagy virtuális sor): a `]album` előtagú token a nem ilyen után áll (`0x004a7ad4`-`0x004a7b09`); azonos besorolásnál a `]facealbum` előtagú áll a nem ilyen után (`0x004a7b0b`-`0x004a7b48`); két arcalbumnál a személyrendezés (`+0xdc`) dönt;
   4. a mód szerinti kulcs (§2), a `+0x165` szerint megfordítva;
   5. a név (`D+0xc`), kisbetűsített ASCII-összehasonlítással, majd a `0x004a76a0` döntése; a megfordítás itt is előjelet vált (`0x004a8039`-`0x004a8046`);
   6. egyenlőségnél (0, illetve `+1`, lásd lent) az összefésülés a korábbi sorindexűt tartja elöl.
5. **A név ága a valódi kódon (B út, QEMU: `0x004a76a0`, 44 névpár).** Az eredmény az egyszerű, kisbetűsített összehasonlítás, **kivéve** ha mindkét név **1800 és 2100 közötti évszámmal kezdődik**, és a számcsoportjaik mind egyeznek: ekkor az eredmény mindkét sorrendben `+1`, azonos nevekre is (`2014 A` ~ `2014 B`, `2014-01-25 Anna` ~ `2014-01-25 Csilla`, `2014_marcius` ~ `2014_aprilis`, `2019_marcius` ~ `2019_marcius`). Ha a számok valamelyike eltér (`2014-01-25` ~ `2014-01-26`), a rendezés szokásos (`-1`/`+1`). Az összehasonlító az egyező számú esetben nem antiszimmetrikus; mivel a `>= 0` a korábbit tartja elöl, az ilyen párok az `albumdata`-sorok eredeti sorrendjében maradnak. A nem a név elején álló év (`x 2014-01-25 A`) és a kis számok (`Album 2` ~ `Album 10`: a szöveg szerinti `album 10` van előbb) nem kapnak külön kezelést. Az összehasonlítás előjeles bájtokon fut (`jl`/`jg`), így a 0x80 feletti bájtok az ASCII elé kerülnének; a tárolt kódolást nem vizsgáltam.
6. **A végeredmény.** A kártyák **dátum szerint növekvő** sorrendben állnak (az újabb hátul); azonos dátumnál a `+0x148` sorrend marad: kategória-prioritás csökkenő, kategórianév, besorolás (virtuális, felhasználói album, arcalbum), név növekvő (kisbetűsített ASCII), azonos számcsoportú, évszámmal kezdődő nevek esetén a táblasorrend. A tulajdonos katalógusában négy virtuális sor azonos dátumú (`]screensaver`, `]updated`, `]history:email`, `]history:upload`: `45772,771782407406`): ezek a nevük (`Képernyővédő`, `Legutóbb frissítve`, `Elküldve e-mailben`, `Feltöltve`) szerinti sorrendbe kerülnének, ha kártyát kapnának.

##### §5 Az album- és a virtuális sor dátuma (`0x0055d730`, `0x00452a30`)

**A két cím nem dátumforrás (A út és hívási kép).** A `0x0055d730` egy sztring-értékadó és -ürítő (`CString` felépítése a `char*`-ból `0x00985ff0`-val, a `param_3+0x14` régi értékének felszabadítása); hívói a sorlétrehozók (`0x004ad010`, `0x004ad220`, `0x004ad570`, `0x004ad680`, `0x00561840`...). A `0x00452a30` a kategória **keresése vagy létrehozása**: a `0x00453970` megkeresi a nevet (`-1` esetén a `0x00452ad0` létrehozza a `catdata` sort, a `state` oszloppal), és ha a név `People`, a sorszámot a `CThumbDB+0x2ea0`-ban gyorsítótárazza. A 38.2.190 §5 utolsó pontja (a két cím "az új sor dátuma") ezzel **cáfolt**.

**Mi igazolható az adatból (B út).** A három katalógus fájlnév nélküli sorai:

| sor | dátum | megfigyelés |
|---|---|---|
| virtuális (`]star`, `]screensaver`, `]updated`, `]history:email`, `]history:upload`, `]unknownface`, `]search`) | időbélyeg: pl. `]updated` `2026-07-18 14:45:36`, `]screensaver` `2026-08-17 23:33:36`, `]search` `2026-08-22 20:36:25` | egyszerre létrejött sorok **azonos** bélyeget kapnak (a tulajdonosnál négy sor `2025-04-25 18:31:22`); a `]search` a legfrissebb: létrehozási vagy utolsó érintési időpont, **nem tartalmi dátum** |
| felhasználói album (`]album:`, üres `filename`) | pl. `2012-02-11 19:00:11`, `2010-12-31 12:16:32`, `2010-11-14 11:42:52` | a név dátumával többnyire egyezik, de nem névből jön: a `2010-10-03 Régi fotók szkennelve BéHának` album dátuma `2010-09-22 21:55:47`, a `2010-10-xx Panoráma fotók...` albumé `2010-09-30 17:56:18`; tartalmi vagy ini-eredetű érték |
| üres token és név | `949998,0` (4501-01-01) | törölt sorok: nincs név, a `0x004aab27` szerint állapot 0, sosem kártya |

Az ini-szinkron (`0x00441ed0`, 7449 bájt) a `[Picasa]` fejlécből `date=`-et olvas (`_atof`, alapérték `949998,0`: `0x0044246a`-`0x0044248d`), a mappákra ez a 38.2.190 §5 szabálya. A 3. virtuális rés (a dátumíró) hívóinak mintaalapú pásztázása (`[x+0x48]` objektum, `mov r, [r2+0xc]`, `call r`) négy helyet adott: `0x00514180` (importálás: `%d-%02d-%02d`), `0x00613b50` (filmkészítő), `0x006e3990` (indítás), `0x006f2fc0` (online album); **az album-létrehozó kódban (`0x004abe70`, `0x004ad220`, `0x004ada80`, `0x0055d120`) nincs dátumírás**.

**Ami nyitott:** a virtuális és a frissen létrehozott albumsor **kezdeti dátumának írója**. Ghidra-kör kell: 0x004ada80 és 0x00441ed0 (az album-szakaszok ága) - a `date` oszlop kezdeti értékének írója az album- és virtuális soroknál; a `0x00441ed0` ini-szinkron album-szakasz feldolgozása (`_sscanf` `0x00441fcc`, `__strnicmp` `0x0044203e`).

##### §6 A rendezés utáni átalakítás (`0x0098b550`, `0x007fc4c0`)

**A függvények.** `0x0098b550` (249 bájt, `ret 0x14`) egy `COleDateTime(év, hónap, nap, óra, perc, másodperc)` jellegű kódoló: `ECX` az év, `ESI` a hónap, a verem a nap, az óra, a perc, a másodperc és a kimeneti `double*`. Érvénytelen bemenetnél (év >= 10 000, hónap 0 vagy 13-tól) a kimenet `949998,0` (`0x00c7ccf8`). `0x0098ba30` a hónapot (`1..12`), `0x0098b9e0` az évet adja egy `0x0098b320`-cal dekódolt `tm`-szerkezet `+0x10`, illetve `+0x14` mezőjéből (érvénytelen dátumnál 0).

**A `0x007fc4c0`** (754 bájt, `EDI` = a `this`, a qshow `+0x2f8`):

1. a `[+0x88]` `double`-tömböt (a kártyadátumok, a qshow `+0x380`) rendezi a `0x0049cd60`-nal növekvően, stabilan; a permutáció a `[+0x98]` tömbbe kerül (`0x007fc4f2`);
2. **minden elemet a hónap első napjára kerekít**, a tömb eredeti sorrendjében, helyben: `0x0098ba30` → hónap, `0x0098b9e0` → év, majd `0x0098b550(év, hónap, 1, 0, 0, 0)` (a verem tetején `1`, alatta három `0`, `0x007fc510`-`0x007fc54d`);
3. a `[+0x90]` tömböt (qshow `+0x388`, a 38.2.25-38.2.34 **"A tömb"**) a rendezett sorrendben tölti: `A[0] = 0`, `A[j] = A[j-1] + ln(max(1 + (d[j] - d[j-1]), 1))`, ahol `d` a kerekített napszám (`0x007fc740`-`0x007fc7a7`: `fld1`, `fsub`, `fadd`, `fcom`, `0x00c0b6a0` = természetes logaritmus).

**B út (QEMU).** (a) A `0x0098b550` 16 bemenettel: `(1899,12,30)` → `0,0`; `(1900,1,1)` → `2,0`; `(1900,3,1)` → `61,0`; `(2000,1,1)` → `36 526,0`; `(2025,4,27,18,30,0)` → `45 774,770833`; `(2024,2,29,12,0,0)` → `45 351,5`; `(2025,13,1)`, `(2025,0,1)`, `(10000,1,1)` → `949 998,0`; `(9999,12,31,23,59,59)` → `2 958 465,999988`. (b) A dekódoló-kódoló ciklus (a `0x007fc510`-`0x007fc54d` pontos hívássorrendje) 17 bemeneten: mind a hónap első napját adta (pl. `45 772,771782` → `2025`, `4` → `45 748,0`; `46 309,3217`, `46 309,3385`, `46 309,443` → `2026`, `10` → `46 296,0`; `949 998,0` változatlan). (c) A **valódi `0x007fc4c0`** hat forgatókönyvön (`bemenet` → `+0x88`, `+0x90`, `+0x98`): mind a három tömb **egyezik** a fenti képlettel (a `+0x90` eltérése < 1e-9). Egy minta: bemenet `[45748,1; 45778,1; 45809,1; 45839,1]` → `+0x88 = [45748; 45778; 45809; 45839]`, `+0x90 = [0; 3,433987; 6,899723; 10,33371]`; azonos hónap kártyái `+0x90`-ben egyenlők (`[46309,3217; 46309,3385; 46309,443; 46296,2]` → `[0; 0; 0; 0]`); a dátum nélküli (`949998,0`) elem a végén `+13,7`-et ad (`[46296,5; 45748,2; 46296,9; 45748,7; 46309,3; 949998,0]` → `[0; 0; 6,308098; 6,308098; 6,308098; 20,022354]`).

**Következmények.**
- **Az "A tömb" lezárva** (a viselkedési lap K9 pontja és a 38.2.25-38.2.34, 38.2.77-78 nyitott kérdése): az **író a `0x007fc4c0`**, a `this+0x90` címen át, ezért nem találtak közvetlen `+0x388` író utasítást a korábbi pásztázások; a tartalom **dátumsor** (hónap-lépcsős, logaritmikusan nyújtott kumulált eltérés), nem sorszám. A `0x007ffc90` az `A[i] / A[n-1]` hányadosokat használja (38.2.34); az **egyenlő hányadosok futama az azonos hónapba eső kártyák csoportja**.
- A kártyadátum a rendezés **után** hónap-pontosságú; a `0x007fee70` `%s %d` (hónapnév és év) felirata ehhez illik. A rendezés kulcsa (§4) a kerekítés előtti, teljes időpontú dátum.
- A dátum nélküli kártya (`949998,0`) a hozzáadott `ln(...) ≈ 13,7` miatt **nyújtja az egész skálát**: a többi kártya hányadosa összesűrűsödik a skála alsó részében.

##### §7 Összevetés a PicasaPy-val és megvalósítási javaslat

| Eredeti | PicasaPy | Eredmény és javaslat |
|---|---|---|
| A szupercsoport (`Név~Alnév` kategória `~` előtti része) lecsukva (a `repository.dat`-ban nincs `super:<név>`) → a kategória sorai nem kártyák (§1). | Az Időrend kategóriát nem ismer (`timeline_controller.py:218-300`); a bal hasáb a `.picasa.ini` `P2category` értékét olvassa (`index/side_pane.py`), a `repository.dat`-ot nem. | **eltér.** **Javaslat: ne valósítsa meg**, amíg a bal hasáb nem kap szupercsoport-állapotot; futásidejű felvétel a polaritásra nincs. |
| A `+0xd8` mód csak az azonos dátumú kártyák sorrendjére és a 3-as módban a rejtésre hat; a végső rend dátum szerint növekvő (§2, §4). | A kártyarend dátum, név, azonosító (`timeline_controller.py:293-300`), a bal hasáb rendezési módjától független. | **egyezik** a végső sorrendben. Teendő nincs. |
| Az üres felhasználói album nem kap kártyát; a kártyaépítés ott megszakad, a hívó eldobja a hibát (§3). | `if not photos: continue` (`timeline_controller.py:281-282`), az üres album kimarad. | **egyezik a kártya hiányában.** **Az eredeti hibaútját (a későbbi kártyák elvesztése, kimaradó fókuszeltolás) ne másolja.** Colab-mérés (üres album + későbbi dátumú mappák) megerősítené. |
| Azonos dátumnál: kategória-prioritás, kategórianév, besorolás, név (kisbetűsített ASCII), azonos számcsoportú, évszámmal kezdődő nevek esetén a táblasorrend (§4). | `(date is None, date, name.casefold(), collectionId.casefold())` (`timeline_controller.py:293-300`). | **egyezik** a dátum és a név szerinti sorrendben; **eltér** a kategória és besorolás szerinti döntésben, az évszám-előtagos nevekben (a PicasaPy névrendezést ad) és a nem ASCII betűk kezelésében (`casefold`). A gyakorlati hatás kicsi (azonos dátum ritka). Javaslat: a döntetlenre `(album ? 0 : 1)` rang beépítése csak akkor, ha a kategória elérhető. |
| A kártyadátum a tárolt `albumdata_date`; mappánál a legkorábbi képidő első beíráskor; albumsornál ini- vagy tartalmi eredetű; virtuális sornál időbélyeg (§5, 38.2.190 §5). | A legkorábbi élő `taken_at`; a `folders.date` és `albums.date` megvan az indexben, az Időrend nem használja. | **eltér** (változatlan a 38.2.190 §6 szerint). A virtuális sor kártyáját továbbra se adja hozzá: a dátum forrása nyitott. |
| A kártyadátum a rendezés után hónap első napja; az `A[i] = A[i-1] + ln(max(1 + Δnap, 1))` és a pozíció `A[i] / A[n-1]` (§6). | `sliderPosition = (dátum_sorszám - első) / (utolsó - első)` lineáris, napokban (`timeline_controller.py:301-333`, `slider_position` a `313-321` sorban); a `dateValue` napsorszám. | **eltér: az eredeti hónap-lépcsős és logaritmikus.** **Javaslat:** a rendezett kártyákra `d = date(év, hónap, 1)`, `A[0] = 0`, `A[i] = A[i-1] + ln(max(1 + (d[i] - d[i-1]).days, 1))`, `sliderPosition = A[i] / A[n-1]`; azonos hónap kártyái azonos helyre kerülnek. A `A[n-1] = 0` esetet (egy hónap, egy kártya) az eredeti védelme nincs megnézve, ezért a PicasaPy-ban `0,0` legyen, és ezt a jegy mondja ki eltérésként. |

**Javaslat a hívónak (kódot nem módosítottam).** Csak a bizonyított pontok:

1. A `sliderPosition` számítása a §6 képlet szerint (a legnagyobb nyereség: ez a sáv pontjainak látható helyét változtatja).
2. A többi pontban (§1, §3, §4) **ne** változtasson: a PicasaPy viselkedése a látható eredményben egyezik, vagy az eltérés megvalósítása becslésre épülne.
3. A virtuális albumok kártyáját ne adja hozzá (§5).

**Kész, ha** (a hívó által kiadott fejlesztői jegyhez):

- [ ] a `sliderPosition` az `A[i] / A[n-1]` képlet szerinti; teszt a mért vektorral: bemeneti dátumok `[45748,1; 45778,1; 45809,1; 45839,1]` → `A = [0; 3,433987; 6,899723; 10,33371]`, tehát a pozíciók `[0; 0,332309; 0,667691; 1]` (hat tizedesre);
- [ ] azonos hónap kártyái azonos pozíciót kapnak (teszt: `[46309,3217; 46309,3385; 46296,2]`);
- [ ] a dátum nélküli kártya viselkedése kimondva (az eredeti nyújtása vagy a PicasaPy 1,0 pozíciója), teszttel;
- [ ] vizuális egyezés: az eredeti `job-239` felvétel dátumsávjának pontjai a PicasaPy hat kártyás készletén (mért eltéréssel; a számolt geometria nem helyettesíti).

**Mérési feladat (Colab, 1 feladat, a hívó adhatja fel):** Ctrl+5 egy katalógusban, ahol egy felhasználói album **üres** és más mappák dátuma későbbi (§3), valamint egy másikban, ahol van lecsukott és kibontott `Név~Alnév` szupercsoport (§1). Mérés: a kártyák neve és sorrendje, a dátumsáv pontjainak helye (az `A[i] / A[n-1]` képlet ellenőrzéséhez).

##### Nyitott kérdések mérlege

Nyitott kérdések: 4 nyílt · 5 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 "csak nyitva"

| Kérdés | Állapot | Mi kell hozzá |
|---|---|---|
| A `+0x1d` jelző forrása (`0x004a4710`) | **LEZÁRVA** (§1) | |
| A `+0xd8` nézetmód értékei (`0x005d9cc0`) | **LEZÁRVA** (§2) | |
| Az üres felhasználói album kártyája | **LEZÁRVA** (§3: kódolvasat és QEMU; futásidejű felvétel nincs) | |
| Azonos dátumú kártyák sorrendje | **LEZÁRVA** (§4) | |
| A rendezés utáni átalakítás és az "A tömb" írója | **LEZÁRVA** (§6) | |
| Az album- és a virtuális sor dátumának kezdeti írója | **NYÍLT** | Ghidra-kör kell: 0x004ada80 és 0x00441ed0 - a date oszlop kezdeti értékének írója az album- és virtuális soroknál (a 0x0055d730 és a 0x00452a30 nem az).` |
| A lecsukott kategória (`catdata` `state`) és a fa nézet futásidejű hatása | **NYÍLT** | a fenti Colab-mérés (a szupercsoport-szabály kódból és adatból lezárt) |
| Az `A[i] / A[n-1]` hányados védelme, ha `A[n-1] = 0` (egy hónap vagy egy kártya) | **NYÍLT** | `Ghidra-kör kell: 0x007ffc90 - az A[i] / A[n-1] osztás nullával szembeni védelme; az utolsó elem 0 esetén a futam- és pontképzés.` |
| A `0xa09d` parancs forrása (a 3-as mód) | **NYÍLT**, nem blokkoló | a gyorsbillentyűk vagy az eszköztár táblázatának keresése; a teljes `.text`-ben nincs közvetlen operandusa |

##### Amit kizártam

- **"A `0x0055d730` és a `0x00452a30` az új sor dátumának forrása"** (38.2.190 §5 utolsó pont): cáfolt (§5): sztring-értékadó, illetve kategória-keresés/létrehozás.
- **"A `+0x1d` a kategória saját kibontottsága"**: cáfolt (§1): a szupercsoport kibontottsága; a `~` nélküli kategóriánál mindig 1.
- **"A kártyasorrend a `+0xd8` móddal változik"**: cáfolt (§4, §6): a kártyák mindig dátum szerint növekvők, a mód csak a döntetlent hangolja.
- **"Az "A tömb" sorszámsor"** (38.2.25): cáfolt (§6): kumulált logaritmikus dátumsor.
- **"A rendezés utáni átalakítás nem érinti a pozíciókat"** (38.2.190 §4 utolsó bekezdés): cáfolt; a `0x007fc4c0` ugyanabban a függvényben állítja elő az "A tömb"-öt a kerekített dátumokból.
- **"A virtuális sorok dátuma tartalmi dátum"**: cáfolt (§5): közös időbélyeg.

##### Bizonyítottság

**Megerősített:** a hat `+0xd8` beállító és értékei (két út: hívóhely-argumentumok és az olvasók; a `0xa09d` neve kivételével); a `0x0049cd60`/`0x0049ecd0` stabilitása és iránya (utasításolvasat és 265 QEMU-rendezés); a `0x0098b550` kódolása és a `0x007fc4c0` kerekítése és `+0x90` képlete (utasításolvasat, a valódi függvény hat forgatókönyvön, a kódoló 33 bemeneten); a `0x00a6aa00` `4`-es visszatérése üres képre (QEMU); a `0x0055d730` és a `0x00452a30` szerepe. **Erős:** a `+0x1d` szupercsoport-jelentése és hatása (a hívási környezet utasításszinten, a kulcs az adatban megtalálható; a polaritás élő felvétellel nem igazolt); a kártyaépítés megszakadása üres albumnál (a hibakód-lánc utasításszinten és részben QEMU-val; felvétel nincs); a döntetlen kulcssorrendje (dekompiláció és oszlopazonosítás; a `D+4`, `D+8` oszlopnevei feltételesek, a név ága QEMU-val mért). **Feltételes:** a `catpri` oszlopnév a `D+8`-hoz; az album- és virtuális sorok dátumának forrása (nyitott).

**Módosított fájlok ebben a szakaszban.** Ez a 38.2.210 szakasz és a `picasa-idorend-viselkedes.md` érintett sorai. Kódot, tesztet, eredeti binárist, felvételt vagy mérőadatot nem módosítottam; az ideiglenes mérőszkriptek és kimenetek a munkafa `.bt/` mappájából törölve.

#### 38.2.220 A #6532 nyolc Colab-mérésének kiértékelése képekből: Space, Ctrl+Space, betöltésjelző, Escape utáni kijelölés (#6532, 2026-11-14)

**Hatókör és módszer.** A 38.2.200 által tervezett nyolc feladat megérkezett eredményének kiértékelése. Forrás: a `6532-colab` mappa `job-662` ... `job-669` almappája; minden képernyőkép 1280x1024, mellettük az `allapot.json` (ablaklista és `dhash`; az `ocr` mező minden rekordban üres) és két videó (`job-664/video__01.mp4`, 100 s, és `job-669/video__06.mp4`, 30 s; mindkettő 15 kép/mp, 1280x1024). Feladat-hozzárendelés: 662 = 02a, 663 = 01a, 664 = 03a, 665 = 02c, 666 = 01d, 667 = 01b, 668 = 01c, 669 = 02b. A képnév alakja `job-663/kepernyo__12.png`; a videóknál az "N. képkocka" az 1-től számozott képkockát jelöli. A képsorszám a 38.2.200 szerinti: az N. kép az (N-1). lépés utáni állapot (ellenőrizve: a job-663 11. képe az első Space után készült, ezen jelenik meg először a OneUp).

**Két út.** *A út:* minden döntő képet megnéztem (a panelre vágott kontaktlap, teljes képernyő, a könyvtárnézeteknél a mappafa, az állapotsor és a tálca). *B út (gépi):* minden képre kiszámoltam a nyers képpontok ujjlenyomatát (MD5), a képpárok különbségének határolótéglalapját (`ImageChops.difference(...).getbbox()`), és a OneUp képének nem fekete téglalapját; a két videót képkockánként dolgoztam fel (átlagos szürkeérték, kockák közti változás, a nem fekete terület határa). A két út a döntésekben egyezik; ahol csak az egyik támasztja alá az állítást, jelzem.

##### 1. Döntéstábla

| Feladat | Kérdés | 38.2.200 jóslata | Mért eredmény (képfájl) | Döntés |
|---|---|---|---|---|
| 01a (job-663) | Space első fotója, szünetelés, 2. és 3. Space | `1/7`, `2019-03-08 09:15`, szünetel; a 2. Space indít, a 3. megállít | 11-12. kép: `1/7`, `2019-03-08 09:15` (`kepernyo__11.png`, `kepernyo__12.png`); a 12-14. kép pixelre azonos (`kepernyo__12.png`, `kepernyo__13.png`, `kepernyo__14.png`); 15-17. kép: `1/7`, `2/7`, `4/7` (`kepernyo__15.png`, `kepernyo__16.png`, `kepernyo__17.png`); 18-20. kép pixelre azonos, `4/7` (`kepernyo__18.png`) | **jóslat igaz** |
| 01b (job-667) | az első fotó a 3 képes kártyán | `1/3`, `2014-11-02 15:30`; Escape után a mappa kijelölt, fotó nélkül | `kepernyo__09.png`, `kepernyo__10.png`: `1/3`, `2014-11-02 15:30`; Escape után `kepernyo__12.png`: `2014_november (3)` mappa kijelölt, `Folder Selected - 3 photos` | **jóslat igaz** |
| 01c (job-668) | az első fotó a 24 képes gyűjteményen | az első fotó; Escape után mappa, fotó nélkül | `kepernyo__16.png`: az 1024x256 méretű `gray_ramp` (a könyvtár első bélyegképe), sorszám nincs a képen; Escape után `kepernyo__18.png`: `PicasaTeszt (24)` mappa ÉS a `gray_ramp.jpg` fotó kijelölt | **az első fotó igaz; a "fotó nélkül" TÉVES** |
| 01d (job-666) | a Ctrl+Space látható hatása | a panel tartalma megváltozik, a OneUp nem nyílik | `kepernyo__08.png`, `kepernyo__09.png`, `kepernyo__10.png`, `kepernyo__11.png` pixelre azonos; `qshow` marad az ablaklistában | **a változás jóslata CÁFOLT** (gyenge nulla, §3) |
| 03a (job-664) | `Preparing timeline...` betöltésjelző | nincs köztes kocka, vagy a köztes kockán nincs jelző | három belépés, mindegyiken legfeljebb egy (majdnem) fekete kocka, jelző nincs (§4) | **jóslat igaz** |
| 02a (job-662) | kijelölés mappafókuszból, Right+Left után | a belépés a `2009_majus` kártyával; Escape után `2009_majus` és `2009_majus_01.jpg` | `kepernyo__07.png`, `kepernyo__08.png`: `2009_majus`; `kepernyo__09.png`, `kepernyo__10.png`: `2014_november`; `kepernyo__11.png`, `kepernyo__12.png`: `2009_majus`; `kepernyo__14.png`, `kepernyo__15.png`: `2009_majus (1)` és `2009_majus_01.jpg` kijelölt | **jóslat igaz** |
| 02b (job-669) | kijelölés a legkorábbi Escape után | ugyanaz, mint 02a | `kepernyo__10.png`, `kepernyo__11.png`: `2009_majus (1)` és `2009_majus_01.jpg` kijelölt; a videón az Escape az első panelkép után 29 képkockával érkezik (§4) | **jóslat igaz** |
| 02c (job-665) | kijelölés `PicasaTeszt` és `Recently Updated` kártyáról | `PicasaTeszt` mappa és első képe; az albumnál két lehetőség | `kepernyo__16.png`: `PicasaTeszt (24)` és `gray_ramp.jpg`; az album: `kepernyo__31.png`: `PicasaTeszt (24)` kijelölt, az `Albums` alatti sor nem, és egy fotó kijelölt; a második belépés kártyája `2009_majus` (`kepernyo__19.png`) | **`PicasaTeszt` igaz; az album mindkét jósolt lehetősége téves** (a harmadik: mappanézet és fotó); a második belépés igaz |

##### 2. Space (01a, 01b, 01c)

1. **A OneUp felület nyílik, a `qshow` marad az ablaklistában** (`job-663/allapot.json`, 11-20. rekord). Fekete teljes képernyő, a fotó természetes méretben, középen: az 800x600-as mintaképek a 240,212 ponttól (nem fekete téglalap 240,212-1039,811: `job-663/kepernyo__12.png`, `job-667/kepernyo__10.png`, `job-666/kepernyo__12.png`), az 1024x256-os `gray_ramp` a jobb szélén az 1151. oszlopig és a 384-639. sorban (`job-668/kepernyo__16.png`).
2. **Vezérlősáv csak az első képen.** A Space utáni első képen halványan látszik az alsó sáv (`Exit Slideshow`, `Timeline`, két forgatógomb, lejátszás, következő, csillag, `Display Time 3 seconds`; `job-663/kepernyo__11.png`, `job-668/kepernyo__15.png`, `job-667/kepernyo__09.png`, `job-666/kepernyo__12.png`: legnagyobb szürkeérték az y >= 940 sávban 29-30), a következő képen már nincs (`job-663/kepernyo__12.png`, `job-668/kepernyo__16.png`, `job-667/kepernyo__10.png`, `job-666/kepernyo__13.png`: 0). A két kép különbsége kizárólag a 274,960-1022,996 sávban van. A sáv a 663-ban később sem tér vissza (`kepernyo__15.png` ... `kepernyo__19.png`: 0).
3. **Szünetel.** A fotó területén (y < 940) nincs különbség a 12-14. kép közt (`job-663/kepernyo__12.png`, `kepernyo__13.png`, `kepernyo__14.png`; köztük legalább 9 s telt el: két várakozás, 3 s és 4 s, plusz két 1,0 s-os szünet), a 667-ben a 10-11. kép (`kepernyo__10.png`, `kepernyo__11.png`), a 668-ban a 16-17. kép (`kepernyo__16.png`, `kepernyo__17.png`) azonos.
4. **A második Space lejátszást indít** (`job-663/kepernyo__15.png`, `kepernyo__16.png`, `kepernyo__17.png`): a kép a qshow-panel 600x480 területére illesztve áll (600x450, a 340,287 ponttól), a felirat `1/7 2019-03-08 09:15`, majd `2/7 2019-03-08 09:32`, majd `4/7 2019-03-08 10:06`. A harmadik Space megállít az aktuális fotón: a `kepernyo__18.png`, `kepernyo__19.png`, `kepernyo__20.png` pixelre azonos, az 800x600-as természetes méretben, `4/7`. A sorszám 2/7 és 4/7 közti ugrása és az időköz: lásd §7 (nem mérhető).
5. **A kezdőfotó azonosítása.** A 01a és 01b képein a fotóba égetett felirat adja az azonosítást (`2019_marcius 1/7 2019-03-08 09:15`; `2014_november 1/3 2014-11-02 15:30`); a 01c-n nincs felirat, ott a `gray_ramp` a könyvtár első bélyegképe (`job-668/kepernyo__18.png` állapotsora: `gray_ramp.jpg`, 1024x256), az azonosság a képi egyezésből következik (vízszintes szürke átmenet, 1024x256), a `1/24` sorszám nem olvasható.
6. **Escape a OneUp-ból** egy lépésben a könyvtárba vezet (`qshow` nincs az ablaklistában: `job-663` 21. rekord, `job-667` 12., `job-668` 18., `job-666` 15.). A kijelölésről: §5.

##### 3. Ctrl+Space (01d, job-666)

- A 8. kép a `2014_november` kártya (a Right és a 2,5 s várakozás után); a Ctrl+Space (8. lépés) utáni 9. kép és a két következő kép pixelre azonos vele (`kepernyo__08.png` = `kepernyo__09.png` = `kepernyo__10.png` = `kepernyo__11.png`, ujjlenyomat `12e73c`, ugyanez a hely a 663, 665, 667, 668 feladatban is). A `qshow` az ablaklistában marad (`allapot.json`, 9-11. rekord), a OneUp nem nyílik.
- **Kontroll.** Az ezután adott sima Space ugyanazt a képsort adja, mint a Ctrl+Space nélküli job-667: `job-666/kepernyo__12.png` = `job-667/kepernyo__09.png`, `job-666/kepernyo__13.png` = `job-667/kepernyo__10.png`, és a végállapot `job-666/kepernyo__15.png` = `job-667/kepernyo__12.png`, mind pixelre azonos. Tehát (a) a billentyűcsatorna a Ctrl+Space után is működött (a Space megnyitotta a OneUp-ot), (b) a Ctrl+Space nem értelmeződött sima Space-ként (azt a OneUp megnyitása követte volna), (c) a `[this+0x3ba]` jelző beírása sem hagyott látható nyomot sem a panelen, sem a következő Space eredményén.
- **A korlát (gyenge nulla).** A képek nem igazolják, hogy a Ctrl+Space a Picasáig ért; a 38.2.200 3.2 pontja ezt előre kimondta. A jóslat "a panel tartalma megváltozik" része a mérés szerint nem teljesült, a "OneUp nem nyílik" része igen.

##### 4. Betöltésjelző és belépési átmenet (03a, 02b videó)

A `job-664/video__01.mp4` három Ctrl+5 belépését képkockánként vizsgáltam (a Ctrl+5 időpontja nincs a felvételen, a belépés a könyvtárkép és az első panelkép határa).

| Belépés | utolsó könyvtárkocka | köztes kocka | első panelkocka | megjegyzés |
|---|---|---|---|---|
| 03a, 1. (hideg) | 311. | 312.: teljesen fekete (legnagyobb szürkeérték 5) | 313. (átlag 30,1, a 328. kockára 26,0) | a 310. kockán a kurzor a `PicasaTeszt` sor fölött áll, a 311. kockán a sor kijelölődik (§7) |
| 03a, 2. | 539. | nincs külön fekete kocka | 540. (átlag 0,3, a panelen kívül nincs 8-nál világosabb képpont; 558. kockára 25,4) | feketéből világosodik |
| 03a, 3. | 774. | 775.: fekete (legnagyobb szürkeérték 8) | 776. (a nem fekete terület 344,372-939,746, tehát a panelen belül) | feketéből világosodik |
| 02b (`job-669/video__06.mp4`) | 28. | nincs | 29. (átlag 27,2) | a 29. kocka már a halvány panel |

- **Egyik köztes vagy első kockán sincs a panel téglalapján (340,272, 600x480) kívül 8-nál világosabb képpont**: se lebegő ablak, se folyamatjelző sáv, se `Preparing timeline...` vagy `Press ESC key on keyboard to abort` szöveg. Ez a 38.2.200 3.3 pontjának jóslata. A 312. kocka teljes képe és a 311-313. kockák kontaktlapja megtekintve.
- **Bezárás.** Escape után a panel feketére sötétedik (job-664: 445-459. kocka, 15 kocka; job-669: 58-73. kocka, 16 kocka), és a kép a job-664-ben a 462., a job-669-ben a 76. kockáig fekete marad, majd a könyvtár két lépésben festődik: az első kocka csak a címsort és a menüt mutatja fekete munkaterülettel (job-664 463.), a másodikon az előző kijelölés látszik (464.: `PicasaTeszt` mappa és `gray_ramp.jpg`), a harmadikon már a végleges (465.: `2009_majus`). A job-669-ben ugyanez 77-79. kocka (a 77-en a fában már a `2009_majus` sor kijelölt, de a tálcán még a `Folder Selected - 7 photos` áll).
- **Az Escape időzítése (02b).** Az első panelkockától (29.) a sötétedés kezdetéig (58.) 29 kocka telt el (29/15 = 1,93 s, a pontosság egy kocka, 0,07 s): az Escape a megnyitó áttűnés (29-44. kocka, a cím a 44. kockára teljes fehér) befejezése UTÁN érkezett, tehát az "Escape az áttűnés közben" állapotot ez a végrehajtó nem adja (ahogy a 38.2.200 1. része előre kimondta).
- **A felirat a nyitás első kockáin.** A fókuszos belépésnél (job-669, 29-34. kocka) a nagy halvány felirat először a belépési mappa gyűjteményét (`2019_marcius`, `2019-03-08 09:15`) mutatja, és a 34-40. kockán úszik át a `2009_majus`, `2009-05-14 10:00` feliratra, miközben a jobb felső cím (`2009_majus`, `May 2009`) az első kockától ezt mutatja. Ugyanabban az időpontban (az első Ctrl+5 utáni kép) fókusz nélkül a nagy felirat tiszta `2009_majus` (`job-663/kepernyo__05.png`), a fókuszos `job-662/kepernyo__07.png` képén még látszik az átúszás maradványa (`9_majus` és `ius` egymásra csúszva).

##### 5. Az Escape utáni kijelölés (02a, 02b, 02c és a Space utáni esetek)

| Job (feladat) | Belépési fókusz | Kártya az Escape előtt | Space? | Mappafa | Kijelölés a főnézetben | Képfájl |
|---|---|---|---|---|---|---|
| 662 (02a) | `2019_marcius` (kattintva, `kepernyo__05.png`) | `2009_majus` (Right, Left után: `kepernyo__12.png`) | nem | `2009_majus (1)` | `2009_majus_01.jpg` | `kepernyo__14.png`, `kepernyo__15.png` |
| 669 (02b) | `2019_marcius` (kattintva) | `2009_majus` (navigáció nélkül) | nem | `2009_majus (1)` | `2009_majus_01.jpg` | `kepernyo__10.png`, `kepernyo__11.png` |
| 664 (03a) | nincs | `2009_majus` | nem | `2009_majus (1)` | `2009_majus_01.jpg` | `kepernyo__08.png`, `kepernyo__12.png`, `kepernyo__16.png` |
| 665, 1. Escape | nincs | `PicasaTeszt` (`kepernyo__14.png`) | nem | `PicasaTeszt (24)` | `gray_ramp.jpg` | `kepernyo__16.png` |
| 665, 2. Escape | `PicasaTeszt` marad az előző Escape-ből | `Recently Updated` album (`kepernyo__29.png`) | nem | `PicasaTeszt (24)`; az `Albums` alatti sor nem kijelölt | egy tájkép-fotó (állapotsor: `_d0ccc81b-5e41-40...967b3dc.jpg`, 1024x1024) | `kepernyo__31.png` (= `kepernyo__32.png`) |
| 663 (01a) | nincs | `2019_marcius` | igen, 3 Space | `2019_marcius (7)` | csak mappa: `Folder Selected - 7 photos`, fotó nincs | `kepernyo__21.png` (= `kepernyo__22.png` = `kepernyo__23.png`) |
| 667 (01b) | nincs | `2014_november` | igen | `2014_november (3)` | csak mappa: `Folder Selected - 3 photos` | `kepernyo__12.png` (= `kepernyo__13.png` = `kepernyo__14.png`) |
| 666 (01d) | nincs | `2014_november` | igen (Ctrl+Space, Space) | `2014_november (3)` | csak mappa: `Folder Selected - 3 photos` | `kepernyo__15.png` (= `job-667/kepernyo__12.png`) |
| 668 (01c) | nincs | `PicasaTeszt` | igen | `PicasaTeszt (24)` | `gray_ramp.jpg` | `kepernyo__18.png` (= `kepernyo__19.png` = `kepernyo__20.png`) |

1. **A belépési fókusz nem számít** (02a, 02b: a `2019_marcius` fókusz ellenére a belépő kártya `2009_majus`: `job-662/kepernyo__07.png`, `kepernyo__08.png`, `job-669/video__06.mp4` 40-46. kocka; és az Escape után sem a belépési mappa jelölődik ki). A fókuszos belépésnél a `qshow` megnyílik (`job-662/allapot.json` 7-12. rekord), tehát a 38.2.200 3.4 pontjának cáfoló feltétele (a `qshow` nem nyílik meg) nem teljesült.
2. **A belépő kártya mindig a legkorábbi (`2009_majus`)**: `job-662/kepernyo__08.png`, `job-663/kepernyo__06.png`, `job-665/kepernyo__06.png`. **A második belépés is `2009_majus`-sal nyílik** (`job-665/kepernyo__19.png`; a 38.2.83 nyitott pontja lezárva).
3. **Közvetlen Escape mappakártyán** (Space nélkül): a kártya mappája és az első fotója kijelölt (`2009_majus` három feladatban, `PicasaTeszt` egyben, és a korábbi job-241-ben a `2021_eltero_fajlido`). A 02b jóslata ("a közbeni navigáció nem számít") igaz: a 02a és a 02b végállapota azonos.
4. **Albumkártya** (`Recently Updated`): a mappafában a `PicasaTeszt (24)` sor kijelölt, az `Albums` alatti `Recently Updated (24)` sor nem, a főnézet a `PicasaTeszt` mappa, és egy fotó kijelölt (`job-665/kepernyo__31.png`). A tálca bélyegképe a `kepernyo__29.png` album-kártyája felső lapjára hasonlít (bolygós tájkép); képpontos azonosítás nem történt. Hogy a `PicasaTeszt` fasort az Escape jelölte-e ki, nem dönthető el (az első Escape után is az volt kijelölt, `kepernyo__16.png`). A job-239 (38.2.81) "a belépés előtti `PicasaTeszt` mappanézet tér vissza" állítása ezzel összhangban van.
5. **Space és Escape után két eset van** (az ellentmondás): `2019_marcius` (7 fotó) és `2014_november` (3 fotó): csak a mappa kijelölt; `PicasaTeszt` (24 fotó): a mappa és az első fotó. A lehetséges magyarázó változók és amit a mért cellák mondanak: (a) a Space: a 663, 666, 667 Space-es esete mappát ad, de a 668 is Space-es, és fotót is ad, tehát a Space önmagában nem magyaráz; (b) a kártya sorszáma: a csak-mappa esetek az 1. és a 2. indexű kártyák, a fotós esetek a 0. és a 4. indexűek, nincs monoton szabály; (c) a fotók száma: 3 és 7 csak-mappa, 1 és 24 fotós; (d) hogy a mappa a belépés előtt látszott-e a főnézetben: a `PicasaTeszt` látszott (fotós), a `2009_majus` nem látszott (fotós, 662), a `2019_marcius` és a `2014_november` nem látszott (csak-mappa). Egyik változó sem ad egyetlen szabályt a kilenc állapotra. Két kimérhető cella hiányzik, amely szétválasztaná őket: Space és Escape a `2009_majus`-on, valamint Escape Space nélkül a `2014_november`-en és a `2019_marcius`-on (§8).
6. **A szomszéd megnézve:** a végállapot minden esetben stabil (a 663, 667, 668 három utolsó képe pixelre azonos, a 665 két utolsó képe is), tehát nem időzítésfüggő késői kijelölés. A könyvtár a kijelölést két lépésben alkalmazza (§4, 464-465. és 77-79. kocka); a job-664 `kepernyo__15.png` képe teljesen fekete, miközben az `allapot.json` 15. rekordjának `dhash` értéke könyvtárnézetet mutat: a képernyőkép és az állapotrekord nem ugyanabban a pillanatban készül.
7. **Mellékes megfigyelés (a 38.2.94 háttérkérdéséhez):** az album-kártya fókuszában a panel hátterében kiszürkített tájkép látszik (`job-665/kepernyo__29.png`), a `PicasaTeszt` kártya fókuszában (2,5 s várakozás után, `kepernyo__14.png`) nem.

##### 6. Eltérések a PicasaPy mostani viselkedéséhez és megvalósítási javaslatok

A kódhelyek a `src/picasapy/app/qml/PicasaPy/` alatt vannak. A javaslatok a hívó által kiadott fejlesztői jegyeknek szólnak; kódot ebben a körben nem változtattam.

| # | Mért eltérés | PicasaPy most | Megvalósítási javaslat | Teszt és elfogadás |
|---|---|---|---|---|
| J1 | Az Időrendből az első Space szünetelő OneUp-ot nyit, a fotó nem lép (`job-663/kepernyo__12.png`, `kepernyo__13.png`, `kepernyo__14.png`); a második Space indít (`kepernyo__15.png` ... `kepernyo__17.png`), a harmadik megállít (`kepernyo__18.png` ... `kepernyo__20.png`). | `MainTimeline.qml:122` `hostWindow.startSlideshow(0)`, `MainSlideshow.qml:60-72`, `SlideshowView.qml:201-215`: `playing = true`, 3 s után lép. | `SlideshowView.start(index, paused)` (alapérték `false`, a többi hívó változatlan): `playing = !paused`. `MainSlideshow.startSlideshow(fromIndex, paused)` továbbadja, `MainTimeline.startTimelineSlideshow` `startSlideshow(0, true)`-t hív. A `SlideshowTiming` csak `playing` mellett fut (`SlideshowTiming.qml:16`), tehát az első fotó áll; a `Keys.onSpacePressed` már `togglePause`-t hív (`SlideshowView.qml:566-570`), így a második Space indít, a harmadik megállít. A vezérlősáv induláskor látszódjon: `slideshowControls.controls.shown = true` és `slideshowControls.autoHideTimer.restart()` (az 1500 ms-os `SlideshowControls.qml:100-105` rejti; az eredetiben a Space után legalább 4,5 s-mal készült képen már nincs sáv: 1,0 s szünet, 2,5 s várakozás, 1,0 s szünet). | `tests/app/test_qml_timeline.py` bővítése: Space az Időrenden: a vetítés látható, `playing === false`, `currentIndex === 0`; az időzítő óráját 3 s-nál tovább léptetve is 0; második Space: `playing`; harmadik: nem; Escape: a vetítés bezár, `timelineOpen` hamis. Elfogadás (látás): a PicasaPy renderelt képe az első Space után egybevetve a `job-663/kepernyo__11.png` és `kepernyo__12.png` képpel (fekete háttér, középre igazított fotó, a sáv csak az elsőn); a kép mérete J7 szerint külön kérdés. |
| J2 | A Ctrl+Space nem változtat a képen (`job-666/kepernyo__08.png` = `kepernyo__09.png` = `kepernyo__10.png` = `kepernyo__11.png`). | `TimelineView.qml:403-405`: a `Qt.Key_Space` ág a módosítótól függetlenül `startCurrentSlideshow()`-t hív. | A Space ág elé: `else if (event.key === Qt.Key_Space && (event.modifiers & Qt.ControlModifier)) { event.accepted = true }` (nincs hatás, és a billentyű nem szivárog tovább). A sima Space marad. | Ctrl+Space után `timelineOpen` igaz, vetítés nincs, a panel renderelt képe pixelre azonos a Ctrl+Space előttivel; utána a sima Space megnyitja a vetítést. Mérce: `job-666` 8-11. képe és a 12. kép egyezése a `job-667/kepernyo__09.png`-nel. |
| J3 | Albumkártyáról Escape után a mappanézet marad (`PicasaTeszt`), az `Albums` alatti sor nem kijelölt, és egy fotó kijelölt (`job-665/kepernyo__31.png`). | `MainTimeline.qml:79-82`: albumnál `hostController.showAlbum(...)`, a főnézet albumra vált. | Ha a `collection.firstPhotoPath` sora (`hostController.photos.rowOfPath`) benne van az aktuális mappanézetben, ne hívjon `showAlbum`-ot, csak jelölje ki a fotót (a `selectedIndex` és a `selectedIndexes` a sor); egyébként marad a mostani út. A mérés csak azt az esetet fedi, amikor az album fotója a belépés előtt nézett mappában van (§8, 02g). | Katalógus, ahol az album fotója az aktuális mappában van: albumkártyáról Escape után a nézet a mappa marad, `selectedIndex` a fotó sora, az `Albums` sor nem aktív; a mappakártyás esetek változatlanok. Mérce: `job-665/kepernyo__31.png` (mappafa, a rács kijelölt fotója, a tálca). |
| J4 | Space és Escape után a `2019_marcius` és a `2014_november` esetén csak a mappa kijelölt (`job-663/kepernyo__21.png`, `job-667/kepernyo__12.png`, `job-666/kepernyo__15.png`), a `PicasaTeszt`-nél a mappa és az első fotó is (`job-668/kepernyo__18.png`). | A Space az indítás előtt ugyanazt a kijelölést végzi, mint az Escape (`MainTimeline.qml:116`): mappa és első fotó. | **Kódváltoztatás most nincs:** az ok nem ismert, a mostani út a közvetlen Escape öt mérésével és a 668-cal egyezik, a 663, 666, 667 eseteivel nem. A §8 három mérése után: ha a Space-mentes Escape a `2014_november`-en és a `2019_marcius`-on is csak mappát ad, a szabály a mappához kötődik (`selectTimelineCollection` kapjon "csak mappa" ágat); ha fotót ad, a Space a tényező, és az `exitSlideshow` Időrendes ágában (`MainSlideshow.qml:94-97`) kell a fotókijelölést visszavonni. | A mérés után: a döntési tábla minden cellájára egy teszt, a `job-663`, `job-667`, `job-668` végállapotával mint mércével. |
| J5 (opcionális, kozmetikai) | Nyitáskor a panel halványból áttűnik (`job-669/video__06.mp4` 29-44. kocka), bezáráskor 15-16 kockán sötétedik, a kép a `job-664/video__01.mp4` 462., a `job-669/video__06.mp4` 76. kockájáig fekete (§4). | Nincs nyitási vagy bezárási animáció a `TimelineView.qml`-ben és a `TimelinePanel.qml`-ben; a `visible` kötés azonnal mutat és rejt. | A `TimelineView` ablak `opacity` értékére 1000 ms-os `NumberAnimation` (a 38.2.85 szerinti 1,000 s) a megnyitáskor (0 -> 1), és bezáráskor a `closed()` jelzés a sötétedés végén. A nyitás kezdete belépésenként eltér (feketéből a 03a 2. és 3. belépésén, halványból az 1. belépésen és a 02b-ben, §4); a javaslat a feketéből világosodó változat. | Időzített teszt: 500 ms-nál az `opacity` 0 és 1 között, 1100 ms-nál 1. Elfogadás (látás): a `job-669/video__06.mp4` 29-46. képkockájával egybevetve. |
| J6 | A betöltésjelző a látható futásban nincs (§4). | Az Időrend QML-nyitó útján nincs folyamatjelző. | **Nincs teendő.** A `DAT_00d67914` kapu értéke csak azt dönti el, mikor jelenhetne meg jelző (nem blokkoló). | Nincs. |
| J7 | A szünetelő OneUp a fotót természetes méretben, fekete teljes képernyő közepén mutatja (800x600 a 240,212 ponttól: `job-663/kepernyo__12.png`; 1024x256 a 128,384 ponttól: `job-668/kepernyo__16.png`), lejátszás közben a 600x480 panel területére illesztve (600x450: `job-663/kepernyo__16.png`). | `SlideshowCurrentImage.qml:79`: `PreserveAspectFit`. Hogy a kis mintaképeket nagyítja-e, nincs mérve. | **Kódjavaslat nincs, két mérés kell:** (1) a PicasaPy renderelt vetítőképe az 800x600-as `2009_majus_01.jpg`-vel a 1280x1024-es képernyőn; (2) az eredeti viselkedése a képernyőnél nagyobb fotónál (§8). | A (1) mérés után dönthető, kell-e változtatás. |

##### 7. Bizonyítottság és korlátok

**Megerősített (két út):** a Space első fotója és szünetelése (A út: a képek a 663, 667, 668 három független feladatban; B út: az ujjlenyomatok és a különbség-határoló, valamint a korábbi job-240 és job-373 mérés, 38.2.82 és 38.2.150); a második Space indít és a harmadik megállít (egy feladat, a képsorozat két útja); a belépő kártya (`2009_majus`) minden belépésnél, a másodiknál is (öt feladat); a belépési fókusz hatástalansága az Escape utáni kijelölésre (662, 669 és fókusz nélkül 664, 665); a betöltésjelző hiánya a látható futásban (A út: a kontaktlapok; B út: a pixelhatárok a három belépésen és a 02b-n).

**Erős:** a Ctrl+Space látható hatásának hiánya (egy feladat; a kontroll a Space-sor pixelre azonos egyezése a Ctrl+Space nélküli job-667-tel); a közvetlen Escape kijelölése (öt mérés); az albumkártya kijelölése (egy mérés).

**Feltételes:** a Space és Escape utáni kijelölés (két egymásnak ellentmondó eset, az ok nyitott); a lejátszás időköze és átmenete.

**Korlátok.**
- A felvételek 15 kép/mp-esek (67 ms); a leütés időpontja nincs a felvételen; az `ocr` mező üres, a feliratokat szemmel olvastam.
- A Ctrl+Space null eredménye gyenge: a képek nem igazolják, hogy a billentyű a Picasáig ért, csak azt, hogy sima Space-ként nem értelmeződött és a következő Space működött.
- A betöltésjelző hiánya a hat kártyás készletre és a látható felületre szól; a `DAT_00d67914` kapu értéke nem dönthető el, és egy 67 ms-nál rövidebb jelző nem zárható ki.
- A lejátszás időköze nem mérhető: a `job-663/kepernyo__16.png` (`2/7`) és a `kepernyo__17.png` (`4/7`) közt két léptetés történt legalább 4 s alatt (a várakozás 3 s plusz az 1,0 s-os szünet); a képek elkészítési ideje nincs a rekordban, így a 3 s időköz sem megerősíthető, sem cáfolható. A `Display Time 3 seconds` felirat (`kepernyo__11.png`) az alapértéket mutatja.
- Az áttűnés a lejátszásban nem látszik a két mintán (`kepernyo__16.png`, `kepernyo__17.png`: éles felirat, nincs szellemkép), de két minta nem dönt.
- A 03a videóján a kurzor a `PicasaTeszt` sor fölött áll (310. kocka), és a Ctrl+5 pillanatában (311. kocka) a sor kijelölődik (`Folder Selected - 24 photos`); a feladat leírása kattintást nem tartalmaz, ezért az eredete nem dönthető el a képekből. Az Escape utáni végállapotot ez nem érinti (`2009_majus`, 465. kocka és `job-664/kepernyo__08.png`).
- A képernyőkép és az `allapot.json` rekordja nem ugyanabban a pillanatban készül (§5.6).

##### 8. Nyitott kérdések és következő irány

A 38.2.200 négy nyílt sora közül az 1-3. lezárult, a 4. szétbomlott (5-7. sor).

Nyitott kérdések: 4 nyílt · 5 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”

| Kérdés | Állapot | Mi kell hozzá |
|---|---|---|
| A Space első fotója és szünetelése az Időrendből | **LEZÁRVA** (§2) | |
| A Ctrl+Space látható hatása | **LEZÁRVA** (§3; gyenge nulla) | |
| A betöltésjelző látható megjelenése | **LEZÁRVA** (§4; a kapu értéke nem blokkoló) | |
| Az Escape utáni kijelölés közvetlen Escape után, mappakártyán | **LEZÁRVA** (§5.3) | |
| Az Escape utáni kijelölés albumkártyáról (az album fotója az előző nézetben van) | **LEZÁRVA** (§5.4) | |
| Space és Escape után: csak mappa, vagy mappa és fotó | **NYÍLT** | a `02d`, `02e`, `02f` feladat |
| Albumkártyáról Escape más belépési nézetből | **NYÍLT** | a `02g` feladat |
| Az Időrendből indított lejátszás időköze és első átmenete | **NYÍLT** | a `08a` feladat (videó) |
| A OneUp képmérete a képernyőnél nagyobb fotónál, és a PicasaPy nagyítása | **NYÍLT**, nem blokkoló | nagy mintakép a mintakészletbe (a hívó dolga), és a PicasaPy renderelt vetítőképe |

**Következő irány megnevezve (a hívó adja fel; mind a bevált váz: `"indulas": "alapallapot"`, `"wine_desktop": true`, `"mintakeszlet": "idorend"`, a három kezdő `var 10` után):**

| Fájl (`6532-<név>.job.json`) | Lépéssor a kezdő várakozások után | Perc | Mit dönt el |
|---|---|---:|---|
| `02d-space-2009-majus` | `ctrl+5`, 3, `space`, 2.5, 4, `Escape`, 2, 2 | 12 | Space és Escape a 0. kártyán (1 fotós mappa): mappa, vagy mappa és fotó |
| `02e-escape-2014-november` | `ctrl+5`, 3, `Right`, 2.5, `Escape`, 2, 2 | 12 | Escape Space nélkül, a `job-667` párja |
| `02f-escape-2019-marcius` | `ctrl+5`, 3, `Right`, 2.5, `Right`, 2.5, `Escape`, 2, 2 | 12 | Escape Space nélkül, a `job-663` párja |
| `02g-album-escape-mas-nezetbol` | `kattint [90,311]`, 2, `ctrl+5`, 3, ötször (`Right`, 2.5), `Escape`, 2, 2 | 15 | albumkártyáról Escape, miközben a belépés előtt a `2019_marcius` mappa látszik |
| `08a-lejatszas-videon` | `felvetel 45`, `ctrl+5`, 3, `Right`, 2.5, `Right`, 2.5, `space`, 2.5, `space`, 20, `space`, 2, `Escape`, 2, 2 | 15 | a lejátszás időköze és az első átmenet 15 kép/mp-en (a fotóváltások közti kockaszám, van-e köztes kocka) |

Döntési szabály a `02d`-`02f` eredményére: ha a `02e` és a `02f` is fotót ad (mappa és első fotó), akkor a Space a tényező, és a `job-663`, `job-666`, `job-667` mappa-csak állapota a OneUp-ból kilépés sajátossága; ha a `02e` és a `02f` is csak mappát ad, a mappa vagy a kártya sorszáma a tényező, és a `02d` mondja meg, melyik csoportba esik a 0. kártya. A mérés után a J4 javaslat konkrét kóddá válik.

**A 38.2.200 3. következő irányához** (a 38.2.160 szerinti nyitott A pontok számának frissítése): a viselkedési lap A listáján az indítási jelzés, a Ctrl+Space és a Space tétele LEZÁRVA, az általános kilépés RÉSZBEN LEZÁRVA; a 38.2.160 12-es számát nem számoltam újra, mert a számlálás alapjául szolgáló lista nincs egyben ebben a fájlban (számlálót nem találtam).

**Módosított fájlok ebben a szakaszban.** Ez a 38.2.220 szakasz és a `picasa-idorend-viselkedes.md` érintett sorai (az állapot dátuma, az Escape-, Space-, diavetítés-időköz-, Ctrl+Space- és betöltésjelző-sor, az új átmenet-sor és az A lista négy tétele). Kódot, tesztet, eredeti binárist, felvételt vagy mérőadatot nem módosítottam; az ideiglenes mérőszkriptek és kimenetek a munkafa `.bt/` mappájából törölve.

#### 38.2.230 Az A tömb osztásvédelme egyetlen hónapnál (#6532, 2026-11-14)

**Hatókör és módszer.** A 38.2.210 §6 szerint az "A tömb" (`[this+0x90]`, a qshow `+0x388`) a hónap-elsőre kerekített, rendezett kártyadátumok kumulált `ln(1 + napi eltérés)` összege, és a `0x007ffc90` az `A[i] / A[n-1]` hányadost használja. Nyitott maradt, mi történik, ha az utolsó elem 0. Három kérdés: (1) van-e osztásvédelem a `0x007ffc90`-ben vagy a hívójában, és hová kerülnek ekkor a dátumsáv pontjai és a fogantyú; (2) mit csinál ugyanekkor a PicasaPy; (3) egyezik-e a kettő. **A út:** utasításszintű olvasat capstone-nal (`0x007ffc90`, `0x007fc4c0`, `0x007fdd00`, `0x007fde80`, `0x009ab690`, `0x009aaae0`, `0x00c29990`, a CRT SSE2-jelző inicializálója és a qshow konstruktorlánca), és függvényenkénti operandus-pásztázás a `functions.csv` határaival (a `0x007f0000`-`0x0080ffff` tartomány 370 függvénye, 39 015 utasítás; a vezérlőszó-utasításokra és a `__controlfp` hívóira a teljes `.text` 20 608 függvénye, 2 556 882 utasítás). **B út:** az eredeti kód `qemu-i386` alatt: a valódi `0x007ffc90` a valódi `0x009ab690` rajzolóval egy 320 x 64-es célbittérképre, és a valódi `0x007fdd00` (a mérőkörnyezet a §4-ben). **C út:** a PicasaPy `timeline_motion.py` és `timeline_controller.py` függvényei futtatva egyhónapos adatokon (§6). Ghidra-kör nem kellett.

| # | Kérdés | Válasz | A út | B út | Fok |
|---|---|---|---|---|---|
| 1 | Mikor 0 az `A[n-1]`? | akkor és csak akkor, ha a rendezett kártyák hónap-elsőre kerekített dátuma mind azonos: egy hónap, egy kártya, vagy minden kártya dátum nélküli | a `0x007fc4c0` ciklusa (`fldz`, `max(1 + Δ, 1)`, `ln`) | a valódi `0x007fc4c0`: azonos hónap kártyái `[0; 0; 0; 0]` (38.2.210 §6) | **megerősített** |
| 2 | Van-e osztásvédelem? | **nincs**: az `fdiv` (`0x007ffd94`) előtt nincs nullateszt, a hívó (`0x00800a30`) csak az időparamétert adja; az egyetlen kitérő az `n = 0` | utasításolvasat, operandus-pásztázás | a valódi függvény `A = [0, ...]`-ra végigfut | **megerősített** |
| 3 | Hová kerülnek a pontok? | `0 / 0` = NaN, `x = 0x80000000`, a vágó kiszűri: **egyetlen pont sem rajzolódik** (SSE2-ágon, maszkolt kivétellel) | `0x007ffd94`-`0x007ffe18`, `0x00c29990`, `0x009aaae0` | 0 megváltozott képpont (§4) | **megerősített** a §3 feltételeivel |
| 4 | Hová kerül a fogantyú? | az egérből (`[+0x728]`), `A`-tól függetlenül; a húzás nem ír kijelölést; a felengedés a 0. kártyára görget (`[+0x514]` kezdőértéke 0) | `0x007fdd00`, `0x007fe1b6`, `0x00803915` | a valódi `0x007fdd00` (§5) | **megerősített** (húzás), **erős** (felengedés) |
| 5 | Mit csinál a PicasaPy? | van védelem (nulla nevezőnél 0,0 arány), de a pontok **láthatóan a sáv bal végére halmozódnak**; a `slider_index` 0-t ad | `timeline_motion.py:357-358,392-393` | a függvények futtatva (§6) | **megerősített** |
| 6 | Egyezik-e? | **eltér a pontokban** (az eredetiben nincs pont); a húzásban és a felengedésben egyezik | | | |

##### §1 Mikor nulla az `A[n-1]`

- A `0x007fc4c0` a `0x007fc740`-`0x007fc7a7` ciklusban `A[0] = 0` (a futó összeg `fldz`-ből indul, `0x007fc4d7`; az első elem előző dátuma önmaga), majd `A[j] = A[j-1] + ln(max(1 + (d[j] - d[j-1]), 1))`. Az eltérés nemnegatív (rendezett dátumok, a `max` 1-re szorít), ezért az `A` nem csökkenő, az utolsó eleme a maximum. `A[n-1] = 0` pontosan akkor, ha minden lépés `ln(1) = 0`, vagyis minden kerekített dátum azonos.
- Ide tartozik: egy hónap több kártyája; egyetlen kártya (`A = [0]`, a ciklus `n = 1`-re is lefut, `A[0] / A[0] = 0 / 0`); minden kártya dátum nélküli (mind `949998,0`, 38.2.210 §6). **Nem** ide tartozik az egyhónapos készlet egy dátum nélküli kártyával: az `ln(...) ≈ 13,7` lépés nem nulla (38.2.210 §6).
- `n = 0` esetén a `0x007fc4c0` nem ír `A`-t (`0x007fc4ca`: `je 0x007fc7a9`), a `0x007ffc90` ciklusát a `test [esi+0x38c], 0xfffffffe` / `jbe` (`0x007ffd6d`, `0x007ffd7b`) kihagyja.

##### §2 Nincs osztásvédelem a `0x007ffc90`-ben és a hívóban

- A ciklus (`0x007ffd81`-`0x007ffe68`): `fld qword [A + i*8]`, `fdiv qword [A + (n-1)*8]` (`0x007ffd8d`, `0x007ffd94`), és rögtön a `fcom` (`0x007ffd98`). Közte nincs `ftst`, `fldz` vagy a nevező vizsgálata; a függvényben a `0x007ffd6d` `test`-je az egyetlen feltétel az `A`-ra.
- A két hívóhely (`0x00800d46`, `0x00801003`, a `0x00800a30`-ban) csak a `trunc(256 * t)` időparamétert adja át (`fmul`, `fistp` `0xc00` vezérlőszóval, `push ecx`, `call`). A `0x007f0000`-`0x0080ffff` tartományban a `+0x388`/`+0x38c` operandusnak két olvasója van, a `0x007fdd00` és a `0x007ffc90`; a `0x00800a30` egyiket sem tartalmazza.
- Az alobjektum (`this+0x2f8`) `+0x90`/`+0x94` mezőjét a `0x007f9000`-`0x007ff000` tartományban a `0x007fc4c0` (író), a `0x007faeb0` (törlés) és a `0x007fb9f0` (nullázó konstruktor) éri el; a `0x007fa590` és a `0x007fc010` találatai méret mezők (a `+0x94`, `+0x98` szélesség és magasság egy másik objektumon), nem az `A`. A `0x007ff000`-`0x00810000` tartomány tizenegy `+0x90`/`+0x94` találata hat más függvényben van (nullteszt vagy `0xf8`-as rekordtömb; a `0x00803d40` és a `0x008054e0` találatait nem követtem egyenként).

##### §3 A NaN útja a pont koordinátájáig

1. **Osztás.** `A[i] = 0` és `A[n-1] = 0` mellett az `fdiv` `0 / 0`: maszkolt érvénytelen-művelet kivételnél a QNaN "valós határozatlan" (`0xfff8000000000000`).
2. **Futamszámláló.** A `fcom qword [esp+0x18]` (az előző arány, kezdetben `-1,0` a `0x00cf3f58`-ról) NaN-nal rendezetlen: `C3 = C2 = C0 = 1`, a `test ah, 0x44` / `jp 0x007ffdaa` (`0x007ffd9e`-`0x007ffda1`) ugrik, a számláló `0` (`0x007ffdaa`). Az `fst [esp+0x18]` (`0x007ffdb8`) a NaN-t teszi előző aránynak, így **minden** iterációban rendezetlen az összehasonlítás, a számláló végig 0, és a `0` ág `vertical_offset = 0`-val rajzol (`0x007ffdf2`).
3. **Koordináta.** Az `fmul dword [esp+0x14]` (`0x007ffdc2`) és az `fiadd` (`0x007ffe14`) NaN-t ad; a `0x00c29990` (`_ftol2_sse`): ha `[0xda1428] != 0`, a `cvttsd2si` (`0x00c299a5`) NaN-ra a "egész határozatlan" `0x80000000`-t adja; különben a `0x00c299c6` x87 ága a `fistp qword` alsó dwordjét, ami NaN-ra `0` (QEMU: `x = 0`). A `[+0x700]` tehát `0x80000000` (SSE2) vagy `0`.
4. **A `[0xda1428]` írója (a 38.2.23 §3 "NINCS MEG" tétele LEZÁRVA).** A CRT SSE2-jelző inicializálója: `0x00bf6035` `call 0x00bf5fd5`, `0x00bf603a` `mov [0xda1428], eax`. A `0x00bf5fd5` `cpuid`-ot futtat (`0x00bf6010`), a `test [ebp-4], 0x4000000` (`0x00bf6019`, az EDX 26. bitje: SSE2) után a `0x00bf5f85` SEH-védetten egy `movapd` utasítást próbál (`0x00bf5f95`; `0xc0000005` vagy `0xc000001d` kivételkód esetén 0). A jelző ezért minden SSE2-képes processzoron és operációs rendszeren 1; a PE-adatban álló 0 a kezdőérték.
5. **A kivétel maszkolt (feltétel).** A qshow építése `_controlfp(_MCW_EM, _MCW_EM)`-t hív: `0x007fa7f0` → (`0x007fa850`) `0x007fb9f0` → (`0x007fbaa2`) `0x007fbd90` → (`0x007fbe74`) `0x007fbce0`, amelynek elején `push 0x8001f`, `push 0x8001f`, `call 0x00c0963e` áll (`0x007fbce4`-`0x007fbcee`): minden x87-kivétel maszkolt, a visszaállítás nincs a függvényben. A CRT négy konstanst töltő `fldcw`-je (`0x00c0b70b`, `0x00c28657`, `0x00c29aeb`, `0x00c29d87`) mind `0x027f`-et tölt a `0x00c43c08`-ról. Az alkalmazáskód 483 `fnstcw` helye (a `0x00bf0000` alatt) mind ugyanaz a minta: `fnstcw`, `or eax, 0xc00` (csonkolás), `fldcw`; maszkbitet egyik sem módosít. A `__controlfp` többi hívóhelye `(0, 0)` lekérdezés vagy tárolt pontosság-/végtelenvezérlési érték visszaállítása (a `0x00d3339c` és `0x00d333b8` táblák értékei `0x300`, `0x30000` jellegűek); a `[0xd333d4]` maszk futásidejű értéke NINCS MEG. Maszkot kibontó hívást nem találtam. A futó Picasa-folyamat tényleges vezérlőszava és szála **NINCS MEG**; a QEMU nem modellezi az x87-kivételek kézbesítését, ezért az `0x027e` vezérlőszavas próba (azonos kimenet) sem döntő.

##### §4 A vágó, a rajzoló és a mérés

- A `0x009ab690` a pont rajzolásakor a cél-téglalapot (`x`, `y`, `x + w`, `y + h` a `[ebx+0x18]`, `[ebx+0x1c]`, `[ebx+8]`, `[ebx+0xc]` mezőkből, `0x009ab69a`-`0x009ab6c0`) a `0x009aaae0` vágónak adja; ha az 3-at ad vissza, a függvény képpont nélkül tér vissza (`0x009ab6cb`: `je 0x009ab81f`). A vágó előjeles összehasonlításokkal metsz: `bal = max(0, 0x80000000) = 0`, `jobb = min(szélesség, 0x80000000 + 7) = 0x80000007` (negatív), és a `cmp ebx, ecx` / `jge` (`0x009aab4a`-`0x009aab4f`) a `bal >= jobb` miatt 3-at ad. Túlcsordulás nincs: a `0x80000000 + 7` 32 biten `0x80000007`.
- **Mérőkörnyezet (B út).** `qemu-i386`, a harness az `picasapy-agent/eszkozok/qemu_harness/hb.py` másolata (a PE szakaszai az eredeti VA-kon, nincs CRT-indítás), `timeout 60`, 1200 MiB memóriaplafon `systemd-run` alatt, FPU control word `0x027f`. Hívás: `EAX = this`, `EDI` = a cél, a verem tetején `p = 256`. A `this` mezői: `+0x6c4 = 104` (a `+0x6c0` tengelykép lépésköze), `+0x6c8 = 104`, `+0x6cc = 40`, `+0x6d0` egy átlátszó (alfa 0) képpuffer, `+0x6d8 = 200`, `+0x6dc = 5`; a `+0x6e8` pont-overlay 7 x 8-as (`+0x6ec = 7` lépésköz, `+0x6f0 = 7`, `+0x6f4 = 8`, `+0x6f8` a fehér, alfa 255 képpontok); `+0x718 = 25`, `+0x72c = 30`; `+0x388`/`+0x38c`: az `A` double-tömb és `2n`; kártyarekordok (`+0x3a8`, `+0x3ac`, 0xf8 bájtos, a `+0` mező 100-103); `+0x510` és `+0x514` kezdőértéke `0x77777777` (őrszem). A többi overlay szélessége és magassága 0, ezért a `0x009ab690` a vágónál korán visszatér. A cél: `[+4] = [+8] = 320`, `[+0xc] = 64`, a képpontok kezdetben mind 0. Stubok (az eredeti `ret` takarítással): `0x007fe7c0` (`ret 4`), `0x007fee70` és `0x007fd180` (`ret 0xc`), `0x007fe540` (`EAX = 1`, `ret 0xc`). Az eredeti kód futott: `0x007ffc90`, `0x009ab690`, `0x009aaae0`, `0x009aab60`, `0x00c29990`, `0x007fdd00`. `[0xda1424] = 1`; `[0xda1428] = 1` (SSE2) vagy `0` (lassú ág); `[0xd695d0] = [0xd695d4] = 1` (MMX-ág) vagy `0` (skalár ág). Korlát: a `this`, a cél és az overlay-objektumok kézzel épülnek; nem valódi qshow-futás és nem képernyőkép.

| `A` | x (`[+0x700]`) | y (`[+0x704]`) | megváltozott képpont | a pontok oszlopai (x) | forrás |
|---|---:|---:|---:|---|---|
| `[0; 3,433987; 6,899723; 10,33371]` (kontroll) | 297 | 21 | 224 | 197-203, 230-236, 263-269, 297-303 | mérés (`qemu-i386`, eredeti `0x007ffc90` és `0x009ab690`) |
| `[0; 3,433987]` (kontroll) | 297 | 21 | 112 | 197-203, 297-303 | mérés (ugyanaz) |
| `[0; 0; 0; 0]` | -2147483648 | 21 | **0** | nincs | mérés (ugyanaz) |
| `[0; 0]` | -2147483648 | 21 | **0** | nincs | mérés (ugyanaz) |
| `[0]` | -2147483648 | 21 | **0** | nincs | mérés (ugyanaz) |
| `[0; 0; 0; 0]`, `[0xda1428] = 0` | 0 | 21 | 56 | 0-6 (mind a négy pont egy helyen) | mérés (ugyanaz) |
| a kontroll, `[0xda1428] = 0` | 297 | 21 | 224 | mint a kontroll | mérés (ugyanaz) |
| skalár pixelút (`[0xd695d0] = 0`): kontroll és `[0; 0; 0; 0]` | 297 és -2147483648 | 21 és 21 | 224 és 0 | mint fent | mérés (ugyanaz) |
| `[+0x38c] = 0` (`n = 0`) | nem írt (0) | nem írt (0) | 0 | nincs | mérés (ugyanaz) |

A kontroll `x` oszlopai az `x_i = trunc(100 * r_i) + 200 - (7 >> 1)` képlettel egyeznek (`r = [0; 0,332309; 0,667691; 1]`: 197, 230, 263, 297), az `y = 21` az `((40 + 2 * 5) >> 1) - (8 >> 1)` alap. Az `A[n-1] = 0` mezőállapotban az `x` mező `0x80000000`, az `y` az alap (nincs 7 vagy 14 pixeles eltolás).

##### §5 A fogantyú és a kijelölés (`0x007fdd00`)

- A `0x007fdd00` hívója a `0x007fde80` egérkezelő (két hívóhely). A `[+0x728]` (a `sliderthumb` `+0x710` objektumának x-e) egyetlen írója a `0x007f0000`-`0x0080ffff` tartományban a `0x007fdd00` (`0x007fde67`); a `+0x710` objektumot egyébként csak a konstruktor (`0x007fac75`), az erőforrás-betöltő (`0x007fb3ce`), a destruktor (`0x007fb6e6`) és a rajzoló (`0x007ffe87`) éri el.
- A `0x007fdd00` az `x`-et `[L, L + W]`-re szorítja és `t = (x - L) / W`-t számol (38.2.23 §3); a gomb helye `[+0x728] = trunc(x_c - (floor(SW / 2) + 3))`, az `A`-tól függetlenül. A keresésben (`0x007fdd95`-`0x007fddce`) `d_i = |A[i] / A[n-1] - t|`; `A[n-1] = 0` mellett minden `d_i` NaN. Az `fcom st(2)` rendezetlen (`C0 = C2 = 1`), a `test ah, 5` / `jp` (`0x007fddbc`-`0x007fddbf`) ugrik, a minimum nem frissül, az `EDX` (a legjobb index) `-1` marad, és a `cmp edx, -1` / `je` (`0x007fddd0`, `0x007fddd5`) kihagyja a `[+0x514]` és a `[+0x510]` írását.
- **Felengedés.** A `0x007fde80` `0x202` ága, ha `[+0x429]` (a sávban kezdődött húzás), a `[+0x514]`-et adja a `0x007fd770`-nek (`0x007fe1b6`-`0x007fe1c3`), amely az `i * [P+0x30] + [P+0x20]` kifejezésből (`0x007fd7b5`-`0x007fd7c9`) számolt paraméterre görget a `0x007fd0c0` animátorrekorddal (`0x007fd7e5`). A `[+0x514]`-et a `0x007fdd00` kivételével semmi nem írja a tartományban (a `0x007fe1b6` olvassa, a konstruktor nem írja), és az objektum a `0x007fa7f0` előtt `_memset(0, 0x890)`-nel nullázódik (`0x008038fb`-`0x00803915`, az `EBX` a `0x00803842`-n nulla), így `A[n-1] = 0` mellett a felengedés a **0. kártyára** görget.

| egér x | `A` | `[+0x728]` | `[+0x514]` | `[+0x510]` | forrás |
|---:|---|---:|---|---|---|
| 250 | kontroll `[0; 3,433987; 6,899723; 10,33371]` | 235 | 1 | 101 | mérés (`qemu-i386`, eredeti `0x007fdd00`) |
| 250 | `[0; 0; 0; 0]` | 235 | változatlan (őrszem) | változatlan | mérés (ugyanaz) |
| 150 (a sávon kívül, balra) | `[0; 0; 0; 0]` | 185 | változatlan | változatlan | mérés (ugyanaz) |
| 250 | `[0]` | 235 | változatlan | változatlan | mérés (ugyanaz) |
| 250 | `n = 0` | 235 | változatlan | változatlan | mérés (ugyanaz) |

A mezők: `L = 200`, `W = 104`, `SW = 25`; `250 - (12 + 3) = 235`, a 150 a sáv bal szélére (200) szorul, `200 - 15 = 185`. A kontrollnál `t = 0,4808`, a távolságok `[0,4808; 0,1485; 0,1869; 0,5192]`, tehát `i* = 1`, a rekord `+0` mezője 101.

##### §6 A PicasaPy ugyanekkor

- `timeline_controller.py:301-321`: a `slider_position` a nem rejtett fotók EXIF-napjai közti lineáris arány; `date_span <= 0` (egy nap, egy kártya) esetén `0.0`, dátum nélküli kártyánál `1.0`, ha van dátumos fotó, különben `0.0`. Nincs osztás nullával.
- `timeline_motion.py:357-358` (`slider_index`) és `:392-393` (`timeline_dot_positions`): `ratios = [value / denominator if denominator else 0.0 for value in values]`, tehát nulla nevezőnél minden arány `0,0`. Ez védelem (nincs NaN, nincs kivétel), de más eredményt ad, mint az eredeti.
- `TimelinePanel.qml:16-20` a `dotPositions(values, 0, szélesség - 4, 7, 28, 0, 10)`-et hívja, a delegált (`:603-619`) `visible: modelData.draw`; a fogantyú (`:620-631`) húzás közben az egérből, egyébként a fókuszkártya `sliderPosition`-jéből kapja a helyét; `TimelineView.qml:277-290`: a húzás csak a `pendingSliderIndex`-et írja, a felengedés `>= 0` esetén `animateTo(…, 4000)`-et indít.
- **Mérés (C út).** `TimelineController._collections_to_qml` négy-négy mappával, a `timeline_motion` függvényei a QML-hívás paramétereivel (`x_start = 0`, `track_span_minus_four = 240`, `dot_width = 7`, `y_top = 28`, `track_spacing = 0`, `dot_height = 10`):

| eset (a kártyák) | `sliderPosition` | pontok `(x, y, rajzol)` | `slider_index(·, 0,5)` |
|---|---|---|---:|
| egy hónap, négy mappa, különböző napok (2025-04-02, 10, 20, 30) | `[0; 0,2857; 0,6429; 1]` | `(-3, 9, igen)`, `(65, 9, igen)`, `(151, 9, igen)`, `(237, 9, igen)` | 2 |
| egy hónap, négy mappa, ugyanaz a nap | `[0; 0; 0; 0]` | `(-3, 9, igen)`, `(-3, 2, igen)`, `(-3, 2, nem)`, `(-3, -5, igen)` | 0 (minden arányra) |
| egy kártya | `[0]` | `(-3, 9, igen)` | 0 |
| egyik fotón sincs dátum (3 mappa) | `[0; 0; 0]` | `(-3, 9, igen)`, `(-3, 2, igen)`, `(-3, 2, nem)` | 0 |
| két hónap (kontroll) | `[0; 1]` | `(-3, 9, igen)`, `(237, 9, igen)` | 0 |

A `timeline_dot_positions` közvetlenül az `A` bemenetre (`[0; 0; 0; 0]`, `[0; 0]`, `[0]`) ugyanezeket a pontokat adja, mint a második és a harmadik sor. A mai lineáris modell az egyhónapos, különböző napú esetben nem fajul el (a pontok szétszóródnak); a degenerált út akkor lesz a gyakori eset, ha a 38.2.210 §7 hónap-lépcsős modellje bekerül.

##### §7 Összevetés és megvalósítási javaslat

| Eredeti | PicasaPy | Eredmény és javaslat |
|---|---|---|
| `A[n-1] = 0`: nem rajzolódik pont (§3, §4). | Nulla nevezőnél a pontok a sáv bal végére halmozódnak, a harmadik rejtett, a negyedik 14 pixellel feljebb (`timeline_motion.py:392-393`, §6). | **eltér.** **Javaslat 1.** |
| Húzás: nincs kijelölésfrissítés, a fogantyú az egeret követi (§5). | A `pendingSliderIndex` húzás közben sem hat a kártyára; a fogantyú az egeret követi (`TimelinePanel.qml:620-631`). | **egyezik.** |
| Felengedés: a `[+0x514]` kezdőértékére, a 0. kártyára görget (§5). | A `slider_index` nulla nevezőnél 0, `animateTo(0, 4000)`. | **egyezik** (a fix 4000 ms eltérése a viselkedési lap 32. sora szerinti). **Javaslat 2:** őrző teszt, hogy a 0 ne változzon. |
| A fogantyú nyugalmi helye felengedés után és fókuszváltáskor: a `[+0x728]` egyetlen írója a `0x007fdd00` (egér). | A fókuszkártya `sliderPosition`-je. | **NYÍLT** (Colab-mérés, lent). |
| A hónap-lépcsős `A[i] / A[n-1]` (38.2.210 §7), `A[n-1] = 0`. | A mai lineáris modell: egy nap vagy egy kártya esetén `0.0`. | **Javaslat 3** a modell bevezetésekor. |

**Következtetés.** Az eredetiben az `A[n-1] = 0` osztása védelem nélküli: a `0 / 0` NaN-ból a pont x-e `0x80000000` lesz, a vágó eldobja, ezért egyhónapos (vagy egykártyás, vagy csupa dátum nélküli) katalógusnál a dátumsávon **nincs pont**. A fogantyút az egér mozgatja, a húzás nem választ kártyát, a felengedés a 0. kártyára görget. A PicasaPy védelme (0,0 arány) a felengedésben ugyanazt adja, a pontokban viszont nem: ott a pontok a sáv bal végére halmozódnak. Az eltérés egyetlen függvény egyetlen ágának javításával megszűnik (Javaslat 1); a húzás és a felengedés változatlan maradhat. **A két független út egyezik:** az utasításszintű olvasat (A) a NaN-útvonalat, a vágó kimenetét és a kijelölés kimaradását adja, és az eredeti függvények QEMU-futtatása (B) ugyanezt méri a kézzel épített objektumon; a B út nem igazolja a futó Picasa vezérlőszavát és a képernyőn látható képet (Nyitott kérdések).

**Javaslat a hívónak (kódot nem módosítottam).**

1. **A pontok elrejtése nulla nevezőnél.** `src/picasapy/timeline_motion.py`, `timeline_dot_positions`, a 392-393. sor helyén:

   ```python
   denominator = values[-1]
   if denominator == 0:
       base_y = ((y_top + 2 * track_spacing) >> 1) - (dot_height >> 1)
       return [{"x": -(2**31), "y": base_y, "draw": False} for _ in values]
   ratios = [value / denominator for value in values]
   ```

   A QML a `modelData.draw`-ra köt (`TimelinePanel.qml:603-619`), ezért változtatás nem kell. A `slider_index` (`:357-358`) **ne** változzon: a nulla nevezőnél adott 0 egyezik az eredeti viselkedéssel (§5). A nem SSE2-ág (`x = 0`, a pont a rajzoló bal szélén) nem másolandó: a CRT-jelző minden SSE2-képes gépen 1 (§3), és a nem SSE2-ág eredménye nem szándékolt viselkedés.
2. **Őrző tesztek** (`tests/app/test_timeline_motion_5377.py`, a `test_timeline_dot_positions_match_picasa_qemu_duplicate_branches` mintájára):
   - `timeline_dot_positions([0.0], ...)`, `([0.0, 0.0], ...)`, `([0.0] * 4, ...)`: egyik elem sem `draw`, `x == -2147483648`, `y` az alap;
   - a kontroll: `[0.0, 0.332309, 0.667691, 1.0]` az `x_start = 200`, `track_span_minus_four = 100`, `dot_width = 7`, `y_top = 40`, `track_spacing = 5`, `dot_height = 8` paraméterekkel: `x = [197, 230, 263, 297]`, `y = 21`, mind `draw` (ez a §4 mért kontrollsora);
   - `slider_index([0.0] * n, ratio) == 0` az `n = 1, 2, 4` és `ratio = 0, 0,25, 0,5, 1` értékekre (a 0. kártyára görgetés mért viselkedésének őrzője).
3. **A vezérlő a 38.2.210 §7 modelljében** (`timeline_controller.py:301-333`): ha az `A[n-1] = 0`, minden kártya `sliderPosition`-je `0.0` (nem NaN, nem kivétel). Teszt (`tests/app/test_timeline_controller.py`): `[2025-04-02, 2025-04-10, 2025-04-30]` és egyetlen kártya mind `0.0`; a dátum nélküli kártya külön tétel (38.2.210 §7 "Kész, ha").
4. **QML-teszt** (`tests/app/qml_functional/`, a `test_idorend_bemutato_5377.py` mintájára): egyhónapos készlet (négy mappa); egyik `timelineDateDot` sem látható; a vezérlőre kattintással (a `timelineSliderMouseArea` press/move/release, nem metódushívással) a fogantyú x-e követi az egeret, és a felengedés után `currentIndex == 0`.

**Kész, ha** (a hívó által kiadott fejlesztői jegyhez):

- [ ] `timeline_dot_positions` nulla nevezőnél nem rajzol pontot; a kontrollsor a mért `[197, 230, 263, 297]`;
- [ ] a `slider_index` nulla nevezőnél 0 marad, őrző teszttel;
- [ ] az egyhónapos QML-teszt a vezérlőre kattintással fut, a pontok láthatatlanságát és a fogantyú egérkövetését méri;
- [ ] vizuális egyezés: az eredeti felvétele egyhónapos katalógusról (alább), mért eltéréssel; a számolt geometria nem helyettesíti.

**Mérési feladat (Colab, 1 feladat, a hívó adhatja fel).** Olyan mintakészlet, ahol minden kártya azonos hónapra esik (legalább négy mappa, különböző napokkal), és egy, ahol egyetlen kártya van. Lépések: `Ctrl+5`, várakozás, képernyőkép; húzás a sávon (`kattint` a sáv közepén, egérmozgatás, felengedés) képernyőképekkel a húzás közben és a felengedés után. Mérés: van-e látható pont a sávon (a gépi kód szerint nincs); követi-e a fogantyú az egeret; a felengedés után melyik kártya áll elől (a gépi kód szerint a 0.); hol áll a fogantyú felengedés után (nyitott kérdés). Ha pont látszik a sáv bal szélén, a §3 5. pontjának kivétel-maszk feltevése téves vagy más szál rajzol.

##### Cáfoló kísérletek és amit kizártam

- **"Az eredeti is 0,0 arányt használ, ezért a pontok a bal szélen állnak, mint a PicasaPy-ban."** Cáfolt SSE2-ágon: `x = 0x80000000`, 0 megváltozott képpont (§4). Csak a nem SSE2-ágon áll `x = 0`-nál, és ott a pont a cél bal szélén (0-6. oszlop) rajzolódik, négy pont egy helyen.
- **"A futamszámláló NaN-nál is nő (az azonos NaN-ok egyenlőnek számítanak)."** Cáfolt: az `y` mind a négy iterációban az alap (21), nincs 7 vagy 14 pixeles eltolás; a `fcom` rendezetlen, a `jp` ugrik (§3 2. pont, §4).
- **"A felengedés `A[n-1] = 0` mellett nem változtat a kijelölésen."** (Az én első olvasatom.) Cáfolt: a felengedés a `[+0x514]`-et olvassa, amelynek kezdőértéke 0 (`_memset`, egyetlen író a `0x007fdd00`), ezért a 0. kártyára görget (§5). Ez az eset egyezik a PicasaPy `animateTo(0)` viselkedésével.
- **"A `0x007ffc90` hívója védi az osztást."** Cáfolt: a `0x00800a30` két hívóhelye csak az időparamétert adja, és a `+0x388`/`+0x38c` operandust a `0x00800a30` nem tartalmazza (§2).
- **"A fogantyú helye az `A`-ból jön."** Cáfolt: a `[+0x728]` az egérből számolódik (`x_c - (floor(SW / 2) + 3)`), az `A` csak a kijelölt kártyát adja (§5).
- **Nem állítom:** a futó Picasa vezérlőszavát és szálát, a `[0xda1428]` futásidejű értékét, a fogantyú nyugalmi helyét, és a képernyőn látott képet; ezek a Colab-mérésre várnak. A 38.2.140 7. pontjában álló "kirajzolva a fókuszgyűjtemény pozíciójában" mondatot (a fogantyú) ez a kutatás nem támasztja alá: a `[+0x728]` egyetlen írója a `0x007fdd00`.

##### Nyitott kérdések mérlege

Nyitott kérdések: 2 nyílt · 1 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 "csak nyitva"

| Kérdés | Állapot | Mi kell hozzá |
|---|---|---|
| Az `A[i] / A[n-1]` osztás védelme, ha `A[n-1] = 0` | **LEZÁRVA** (§2-§5; a futásidejű kép nincs mérve) | |
| A kivétel-maszk, a `[0xda1428]` és a rajzoló szál értéke a futó Picasában; a képernyőn látható eredmény (nincs pont) | **NYÍLT** | a fenti Colab-feladat (egyhónapos katalógus) |
| A fogantyú nyugalmi helye felengedés után és fókuszváltáskor | **NYÍLT** | ugyanaz a Colab-feladat (húzás és felengedés képernyőképei) |

##### Bizonyítottság

**Megerősített:** az `A[n-1] = 0` feltétele (utasításolvasat és a valódi `0x007fc4c0` QEMU-mérése a 38.2.210 §6-ban); az osztásvédelem hiánya a `0x007ffc90`-ben és a `0x00800a30` hívóhelyein (utasításolvasat, operandus-pásztázás, a valódi függvény lefut); az `x = 0x80000000` és a pont nélküli kép a mért objektumon (a valódi `0x007ffc90` és `0x009ab690`, 0 megváltozott képpont); a fogantyú x-e az egérből és a kijelölés kimaradása (a valódi `0x007fdd00`); a PicasaPy-oldali kimenetek (futtatva). **Erős:** a felengedés a 0. kártyára görget (utasításolvasat, `_memset`, az egyetlen író; a `0x007fd770` nincs QEMU-ban futtatva); a vezérlőszó maszkolt állapota (`_controlfp(_MCW_EM, _MCW_EM)` a qshow-építés láncában, a CRT `0x027f` konstansa). **Feltételes:** az SSE2-ág a futó folyamatban (a CRT-inicializáló kódja alapján; az értéke nincs mérve); az a feltevés, hogy az építés és a rajzolás ugyanazon a szálon fut. **NINCS MEG:** a futó folyamat vezérlőszava, a fogantyú nyugalmi helye, a képernyőkép.

**Módosított fájlok ebben a szakaszban.** Ez a 38.2.230 szakasz és a `picasa-idorend-viselkedes.md` érintett sorai (a dátumsáv-sor utáni új `A[n-1] = 0` sor és az A lista "A tömb" tétele). Kódot, tesztet, eredeti binárist, felvételt vagy mérőadatot nem módosítottam; az ideiglenes mérőszkriptek, ELF-fájlok és kimenetek a `$SCRATCH` mappából törölve.

### 38.2.240 A Space és Escape utáni kijelölés, és az albumkártya Escape-je: a 02d-02g mérés (#6532)

**Mérés:** Colab job-676 (`02d`), job-677 (`02e`), job-678 (`02f`), job-679 (`02g`), 2026-11-14; a lépéssor a 38.2.220 tervtáblája szerint. A `08a` (job-680) sémahiba miatt nem futott (`var` > 10 mp), újra feladva: job-681.

| Feladat | Lépéssor | Utolsó kép | Kijelölés az Időrend után |
|---|---|---|---|
| `02d` | 2009_majus kártya, Space, Escape | job-676 `kepernyo__12.png` | csak a mappa (a tálcán „Folder Selected - 1 photo”, a fotó keret nélkül) |
| `02e` | 2014_november kártya, Escape Space nélkül | job-677 `kepernyo__11.png` | a mappa és az első fotó (a fotón kijelölő keret, a tálcán „Selection”) |
| `02f` | 2019_marcius kártya, Escape Space nélkül | job-678 `kepernyo__13.png` | a mappa és az első fotó |
| `02g` | a fókusz a `Recently Updated` kártyán (job-679 `kepernyo__18.png`), Escape | job-679 `kepernyo__21.png` | a korábbi nézet (PicasaTeszt) marad, csak a mappa kijelölt („Folder Selected - 24 photos”) |

**Következtetés a 38.2.220 döntési szabálya szerint:** a `02e` és a `02f` fotót is ad, tehát a **Space a tényező**. Közvetlen Escape után a kártya mappája és első fotója kijelölt; a Space-szel megnyitott OneUp-vetítésből kilépve csak a mappa (job-663, job-666, job-667 és most a job-676: négy egyező eset). Egy ellentmondó eset marad: a job-668 (PicasaTeszt, Space, Escape) a mappát és az első fotót is kijelölte. Ennek oka nem ismert; a megvalósítás a négy egyező mérést követi, és a PicasaTeszt-esetet külön jelzi.

**Az albumkártya kérdése (38.2.220 J3) helyesbítve:** a mintakatalógusban az egyetlen album a virtuális `Recently Updated` (a bal hasábban „Albums (1)”). A job-665 31. képe is ezen a kártyán készült (`kepernyo__29.png`: „Recently Updated, November 2026”), tehát a J3 nem felhasználói albumot mért. A virtuális kártya Escape-viselkedését (a korábbi nézet marad) a #6902 már megvalósította. A fotókijelölés a két mérésben eltér: a job-665-ben egy fotó kijelölt, a job-679-ben csak a mappa. A J3 javaslat ezért visszavonva, a #6909-ből kivéve. Valódi felhasználói album Escape-viselkedése nincs mérve, mert a mintakatalógusban nincs ilyen album.

### 38.2.250 Az albumsor és a virtuális sor dátumának írója (#6532)

**Hatókör és módszer.** A kérdés: ki és mikor írja az albumsorra és a virtuális sorra a kártyadátumot adó `albumdata_date` értéket, a tagok melyik időbélyegéből számolódik, és változik-e később. A kiindulás egy korábbi, ellenőrizetlen gépi jelentés volt; az ékezet nélküli szöveg és a benne idézett sorszámok **nem megbízható adat**, minden állítását ellenőriztem (§5). **A út:** a friss Ghidra-kimenet (`picasapy-agent/referencia/ghidra/2026-11-14-6532-colab-decomp-3.txt`: `0x004ada80`, `0x00441ed0`, `0x007fc4c0`) és utasításszintű olvasat (capstone, `eszkozok/pe_dis.py`) azokra a címekre, amelyek nincsenek dekompilálva (`0x00441760`, `0x00441ac0`, `0x00443c00`, `0x004edf60`, `0x0055d070`, `0x0055d320`, `0x0055cf70`, `0x004ad220`, `0x006dc030`, `0x006db580`, `0x00662700`, `0x0098b6e0`); három teljes `.text`-pásztázás a `paszta.py` memóriakapuja alatt (mért csúcs 45 MiB): a "date" kulcs (`0x00c80d7c`) közvetlen használatai, a `0x006a5c60` hívói, és a `[x+0xc]` rés hívásai dupla argumentummal. **B út:** adat, három katalógus (`research/testdata`: `Picasa2/db3`, `Picasa2-arcok/Picasa2/db3`, `1557-masolat-mentese/db3-utana/db3`) a PicasaPy `pmpimport` olvasóival (`read_table`, `read_thumb_index`); a FILETIME-ok `Europe/Budapest` helyi időre váltva (a Picasa a `TzSpecificLocalTimeToSystemTime`-ot `NULL` zónával hívja, `pmp-database.md` 10.3), ±1,5 s tűréssel. Becsült értéket nem használtam. A mérőszkriptek a `$SCRATCH/6532g` mappában készültek, a szakasz végén törölve.

| # | Kérdés | Válasz | A út | B út | Fok |
|---|---|---|---|---|---|
| 1 | A `0x00441760` melyik időbélyeget veszi a tagok közül? | a tag `thumbindex`-rekordjának **1. FILETIME-ja** (a `0x004edf60` leírójának `+4/+8` szava), a legkisebb; ez a kép metaadat-dátuma (EXIF `DateTimeOriginal`), a beolvasó lefutása előtt vagy metaadat nélkül a beolvasáskori fájlidő | `0x00441760`, `0x004edf60`, `0x0040f980`, `0x004eeb10` | 2279 mappa: a tárolt dátum 86,1%-ban az 1. mező minimuma, 44,0%-ban a 2.-é | **megerősített** |
| 2 | Rögzített-e a beírt dátum, van-e más író? | igen: az automatikus számolás csak `0,0`-nál fut; az ini-szinkron dátumírása csak sor-létrehozáskor; az Album tulajdonságai ablak a betöltött értéket írja vissza; kép törlésekor és hozzáadásakor nincs író. Más írók: lista (§3) | `0x00441ac0`, `0x00441ed0`, `0x0055d320`, `0x006dc030` | a tárolt dátum a mai minimumtól mindkét irányban eltér (156 korábbi, 161 későbbi), az export-mappák a metaadat-olvasás előtti értéket őrzik | **megerősített** (automatikus út, ini, ablak), **erős** (törlés) |
| 3 | A virtuális sorok dátuma | a **sor létrehozásának helyi ideje** (1 s felbontás), nem tartalmi; a `]search` soré minden kereséskor a pillanatnyi idő | `0x0055cf70`, `0x0055d320`, `0x0098b6e0`, `0x00662888` | 40 virtuális sorból 0 egyezik bármely képidővel; a vele együtt létrejött sorok azonos másodpercet viselnek | **megerősített** |
| 4 | Összevetés a PicasaPy-val | három igazolt eltérés (EXIF nélküli kép, virtuális sor, rögzítettség); lásd §6 | | | lásd §6 |

##### §1 Ki írja a `date` oszlopot az albumsorra (A út)

A getter és az író oszlopa ugyanaz (38.2.190 §5): az `IThumbDB` 3. rése, `0x004460a0` (`0x004460c3`-`0x004460d8`: `0x006a5c60(tábla, "date", sor, double)`; a bool argumentum nem nulla értékénél az ini is íródik). A teljes `.text`-ben a `0x006a5c60` két hívója közül egyetlen kapja a "date" kulcsot (`0x004460d8`), tehát a `0x006a5c60`-on át a rés az egyetlen író; közvetlen gyorsítótár-írás a `0x00441ed0`-ban van (lent 5. pont), más közvetlen írót nem kerestem.

1. **`0x004ada80(útvonal, &sor)`**, a sorfoglaló. Az első argumentum **útvonal-mutató**, nem jelző: nulla esetén felhasználói album (`0x004adeeb`-`0x004adefc`: `fldz`, `fstp [esp]`, `call 0x00443c00`), nem nulla esetén mappa (`0x00441ed0(CThumbDB, sor, 1)`, a `push 1` a `0x004ade36` címen). Hívói: `0x004b9fb7` (`push 0`; a `CAlbumState::newalbum` útja, `picasa-menu-parancsok-viselkedes.md`), `0x0055d183`, `0x0055f1cc`, `0x00560679`.
2. **`0x00443c00`**: a sor mezőit az `IThumbDB` résein írja (`[+4]` `0x00443c1c`, `[+8]` `0x00443c2c`), majd a dátumot a `[+0xc]` réssel (`0x00443c34`-`0x00443c41`: double `0,0`, bool 0). Ez a nyers kezdőérték.
3. **`0x00441ac0(CThumbDB, sor)`**, az automatikus dátum: a getterrel (`[+0x20]`, `0x00441ada`) olvas, majd `fldz` + `fcomp` + `test ah, 0x44` + `jnp` (`0x00441ae0`-`0x00441aeb`): **csak ha a dátum pontosan `0,0`**, folytatja; különben `xor eax, eax`, `ret 4` (`0x00441aed`-`0x00441af4`). A számolás a `0x00441760` (kimeneti kezdőérték `949998,0`, `0x00441af7`-`0x00441b08`); sikernél a `[+0xc]` réssel írja, bool 0 (`0x00441b18`-`0x00441b24`: csak az adatbázis, az ini nem). Hívói: `0x004aa9f0` (`0x004aadc9`), `0x00441e00`, `0x0055d320` (`0x0055d41b`).
4. **`0x0055d320`**, a sor mezőinek visszaírója egy leíróból (ESI a leíró): a leíró szövegmezői (`+0x14`, `+0x18`, `+0x1c`, `+0x20`; az `IThumbDB` `[+4]`, `[+8]`, `[+0x10]` résein és a `0x004448d0`-on át), majd a dátum. Ha a leíró `+0x30` jelzője nulla, a dátum a leíró **`+0x28`** mezője (`0x0055d422`-`0x0055d429`); ha nem nulla, `0,0` és a `0x00441ac0` (`0x0055d405`-`0x0055d41b`). A `+0x28` forrása kétféle: (a) a leíró konstruktora, `0x0055cf70`, a **pillanatnyi helyi idővel** tölti (`0x0055cfa3` `call 0x0098b6e0`, `0x0055cfa8`-`0x0055cfaf` `fstp [esi+0x28]`, `0x0055cfb7`/`0x0055cfbb`: `+0x30 = 0`, `+0x31 = 1`); a `0x0098b6e0` a `__time64` és a `_localtime64` után a `0x0098b550(év, hónap, nap, óra, perc, mp)` hívással készít változatidőt, 1 s felbontással; (b) a `0x0055d070` (meglévő sor betöltése leíróba) a sor **tárolt dátumát** olvassa be (`0x0055d0df`-`0x0055d0e2`: getter `[+0x20]` a `[leíró+0x28]`-ba), és `+0x30 = 0`-val indul (`0x0055d0ab`). A `+0x30` az "automatikus dátum" jelző: az Album tulajdonságai ablak (`0x006dc030`) a betöltött `+0x28`-at elmenti (`0x006dc082`-`0x006dc08c`), a párbeszéd (`0x008496c0`) után összeveti (`0x006dc0e1`-`0x006dc0ea`), és ha a felhasználó átírta a dátumot, a jelzőt nullázza (`0x006dc0ef`).
5. **`0x00441ed0(CThumbDB, sor, jelző)`**, a mappa `.picasa.ini` `[Picasa]` szakaszának szinkronja: a `date=` kulcsot `_atof`-fal olvassa (`0x00442456`-`0x0044248d`, alapérték `949998,0`), az alapértéket `0,0`-ra cseréli (`0x004433ff`-`0x00443416`), és a dátumot a `+0xc10` oszlopba írja közvetlenül (`0x00443689`-`0x00443697`, azonosnál kihagyja: `0x004436b0`-`0x004436c4`), **de csak ha a 3. argumentum nem nulla** (`0x004433f1`: `cmp byte ptr [esp+0xabc], 0`, `0x004433f9`: `je 0x443725`). A 3. argumentum a sor létrehozásakor 1 (`0x004ade36`), a betöltő (`0x0047c560`) újraolvasásakor 0 (`0x0047c72e`: `push 0`). Albumszakaszt (`[.album:...]`) nem dolgoz fel.
6. **A virtuális sor létrehozása.** A `0x004ad220` (38.2.190 §1/2: `]star`, `]screensaver`, `]updated`, `]history:*` hívói a `0x004ad430`, `0x004ad4e0`) a `0x0055cf70` konstruktort hívja (`0x004ad267`), a `+0x30`-at nem állítja, majd a `0x0055d120`-at (`0x004ad326`), amely a `0x004ada80`-on át sort foglal (`0,0`, 1. pont), és a `0x0055d320`-szal (`0x0055d2d2`) a leíró `+0x28` pillanatnyi idejét írja be. A személy- és arcalbumokat (`People`, `]facealbum:`, `]expeople:%d`) a `0x004ad010`, `0x00561840`, `0x00644bc0`, `0x00645350` ugyanezzel a konstruktorral hozza létre.
7. **A `]search` sor** (`0x00662700`, a keresés kezelője `0x00662b20`): a `0x00662867` `0x0098b6e0`, majd a `[+0xc]` rés (`0x00662879`-`0x00662888`, bool 0): a dátum a keresés pillanatnyi ideje, minden keresésnél.
8. **Kézi és külső írók:** a Mappa/Album tulajdonságai `autodate` kezelője (`0x00849dc0` → `0x00441760`, `0x00849e54`; eredménye a `date` tulajdonságba, `[eax+0xe8]`, 38.2.190 §5), az online album (`0x006f2fc0`, `0x006f3411`, bool 1), az importálás és az indítás hívóhelyei (38.2.210 §5; ezeket most nem olvastam újra). Nem azonosított `[+0xc]` hívás, dupla argumentummal: `0x00452305` (a `0x00451ff0` belsejében, `949998,0` értékkel) és `0x0055822a` (a `0x00557ff0` belsejében, NaN-védelemmel).

A 38.2.210 §5 "az album-létrehozó kódban (`0x004abe70`, `0x004ad220`, `0x004ada80`, `0x0055d120`) nincs dátumírás" mondata **helyesbítve**: a dátumot a `0x004ada80` alatti `0x00443c00` (`0,0`) és a `0x0055d320` (pillanatnyi idő vagy `0,0` + automatikus) írja. A korábbi mintapásztázás az `[x+0x48]` objektumot közvetlenül betöltő alakot kereste, a `lea esi,[ebp+0x48]` és a leírón át hívott alakot nem fogta.

##### §2 Melyik időbélyeg: a rekord 1. FILETIME-ja (két út)

**A út, utasításszint.**

| lépés | cím | tény |
|---|---|---|
| a tagok listája | `0x00441790`, `0x004417b2`-`0x004417b9`, `0x00441819`-`0x00441823` | `[[this+0x48]+0x2c](sor, &lista)`; a lista mutatója `[+0x64]`, az elemszám `[+4] >> 1`; nincs lista vagy nulla elem: visszatérés `-1` (`0x004417b9` → `0x00441875`-`0x0044187e`) |
| a ciklus | `0x00441890`-`0x00441a18` | minden taghoz `edi = lista[ebp]` (`0x00441911`); ha `edi < [this+0x4ec] >> 1` (`0x00441960`-`0x00441971`), `0x004edf60(EAX = edi, this+0xf8, &leíró)` (`0x004419bf`, a leíró `esp+0x24`) |
| mit olvas | `0x004419ca`-`0x004419d2` | a leíró **`+4/+8`** szavait (`[esp+0x28]`, `[esp+0x2c]`); a `+0xc/+0x10` szavakat (`[esp+0x30]`, `[esp+0x34]`) a ciklus csak nullázza (`0x00441988`, `0x0044198c`), olvasni nem olvassa |
| minimum | `0x004419d6`-`0x004419e6` | a 64 bites pár legkisebb értékét tartja; a `0` jelentése "még nincs" (`0x00441892`, `0x004419c8`) |
| átalakítás | `0x00441a22` | `0x0098b650`: FILETIME → helyi `SYSTEMTIME` → változatidő (`0x00441a2e` `fstp [eax]`) |
| a rekordolvasó | `0x004ee08a`-`0x004ee0a2` | `0x004edf60` a rekord `+4/+8` szavait a leíró `+4/+8`-ba, a `+0xc/+0x10` szavait a leíró `+0xc/+0x10`-be másolja: a két mező külön, és a `0x00441760` az elsőt kéri |
| a mező írói | `0x0040f9b6`-`0x0040f9db`; `0x00427844`, `0x00427898`, `0x004eeb10`; `0x004ef3c0`, `0x004ef5a0` | a rekordépítő (`0x0040f980`, a pásztázó `0x004e753f`-`0x004e756a` hívja) a `ftLastWriteTime`-ot **mindkét** mezőbe írja (`+4/+8` és `+0xc/+0x10`); a képbeolvasó a `0x37` metaadat-kulcsot (EXIF `DateTimeOriginal`, `picasa-metaadat-tulajdonsagok.md` 3.) kéri, és sikernél a `0x004eeb10`-zel **csak a `+4/+8` párt** írja felül; a Dátum és idő beállítása nem-JPEG ága ugyanezt a párt módosítja (`pmp-database.md` 15.1) |

⇒ A kártyadátum forrása a rekord 1. mezője: **felvételi idő, fájlidő-tartalékkal**, és a tartalék a *beolvasáskori* fájlidő (az építő kezdőértéke), amelyet a metaadat-olvasó felülír, ha a képnek van `DateTimeOriginal`-ja. Közvetlen EXIF-olvasás nincs a `0x00441760`-ban.

**B út, adat.** A mappasorok (`albumdata_filename` nem üres) minimuma a két mezőre, a tárolt dátumhoz hasonlítva:

| katalógus | összehasonlítható sor | 1. mező minimuma egyezik | 2. mező minimuma egyezik | a két minimum eltér | ebből csak az 1. | ebből csak a 2. | egyik sem |
|---|---:|---:|---:|---:|---:|---:|---:|
| `Picasa2` | 2279 | **1962 (86,1%)** | 1003 (44,0%) | 1081 | **949** | 5 | 127 |
| `Picasa2-arcok` | 103 | 68 (66,0%) | 82 (79,6%) | 39 | 6 | 20 | 13 |
| `1557-masolat-mentese` | 101 | 67 (66,3%) | 79 (78,2%) | 41 | 8 | 20 | 13 |

A nagy katalógusban az 1. mező dönt (949 a 5 ellen, ahol a két minimum különbözik). A két kis katalógusban a "csak a 2." sorok (20 + 20) **mind** `\export\` útvonalú mappa (golden-kit kimenetek, frissen kiírt fájlok), mindegyiknek van `.picasa.ini`-horgonya (`albumdata_inisync` nem nulla); további 11-11 export-mappa egyik minimummal sem egyezik. Értelmezés (erős, nem megerősített): az export-mappa dátuma akkor számolódott, amikor a kiírt fájlok rekordjában az 1. mező még a beolvasáskori fájlidő volt (az építő mindkét mezőbe ezt írja, `0x0040f9b6`-`0x0040f9db`), és a dátum **megmaradt**, amikor a metaadat-olvasó később a forrásképek korábbi `DateTimeOriginal`-jára cserélte az 1. mezőt. Ez egyszerre erősíti meg, hogy a `0x00441760` az 1. mezőt kéri (az akkori értéke a fájlidő volt), és hogy a tárolt dátum nem követi a tagok későbbi változását (§3). A `.picasa.ini` `date=` kulcsa ugyanezt az értéket adhatta (az ini nem elérhető ezekhez a mappákhoz), ez a következtetést nem változtatja: a tárolt érték nem a mai minimum.

##### §3 Rögzítettség: ki változtathatja a beírt dátumot

| író vagy esemény | változtat-e | bizonyíték | fok |
|---|---|---|---|
| automatikus számolás (`0x00441ac0`) | **csak `0,0`-nál** | `0x00441ae0`-`0x00441aed`; hívói: §1/3 | megerősített |
| ini-szinkron (`0x00441ed0`) | **csak sor-létrehozáskor** (`jelző = 1`); a betöltő újraolvasása (`jelző = 0`) a dátumot nem érinti | `0x004433f1`-`0x004433f9`, `0x004ade36`, `0x0047c72e`, `0x0047c560` | megerősített |
| Album tulajdonságai ablak (átnevezés, leírás, hely) | **nem**, ha a felhasználó a dátumot nem írja át: a betöltött értéket írja vissza (a setter azonos értéknél kihagyja, `0x006a5d95`-`0x006a5db1`); a jelző bekapcsolt állapotában `0,0` és újraszámolás | `0x006db63d` (`0x0055d070`), `0x006dc082`-`0x006dc0ef`, `0x006db68c` (`0x0055d320`), `0x0055d422`-`0x0055d429` | erős (a `0x008496c0` párbeszéd belsejét nem olvastam) |
| kép törlése, kép hozzáadása | **nincs író**: a vizsgált hívási alakok között nincs olyan, amely a tagság változásához kötődne | a `[+0xc]` rés hívói (`0x00441b24`, `0x00443c41`, `0x0055d405`, `0x0055d429`, `0x00662888`, `0x006f3411`); a `0x00441ac0` kapuja | erős (negatív, csak a pásztázott hívási alakokra) |
| a tárolt dátum a mai tagokhoz képest | a nagy katalógusban 317 mappa különbözik az 1. mező mai minimumától: **156 korábbi, 161 későbbi**; a két irány együtt azt mutatja, hogy a tárolt érték sem a hozzáadást, sem az eltávolítást nem követi | B út, `Picasa2` | erős (más magyarázat: kézi beállítás, ini `date=`) |
| `]search` | minden kereséskor a pillanatnyi idő | `0x00662867`-`0x00662888` | megerősített |
| autodate parancs, kézi beállítás, online album | igen (felhasználói vagy külső művelet) | `0x00849dc0`, `0x006f3411` | megerősített (a hívóhely) |

A korábbi jelentés "csak `0,0` esetén számol újra" állítása az **automatikus** útra igaz; a rögzítettség többi része (ini-szinkron jelzője, az ablak visszaírása) a jelentésben nem szerepelt.

##### §4 A virtuális sor és a felhasználói album dátuma (B út és a 38.2.210 §5)

**Mit mond a 38.2.210 §5:** a `0x0055d730` és a `0x00452a30` nem dátumforrás; a virtuális sorok közös időbélyeget kapnak (a tulajdonos katalógusában négy sor `2025-04-25 18:31:22`), a `]search` a legfrissebb; a felhasználói albumsor dátuma "tartalmi vagy ini-eredetű"; az író nyitott maradt. **Ezt a §1 lezárja:** a virtuális sor dátuma a leíró-konstruktor pillanatnyi helyi ideje (`0x0055cf70`), a `]search`-é a keresés ideje.

**Mérés** (mindhárom katalógus, a `]`-tokenű, fájlnév nélküli sorok, nem `]album:`): 40 sor; a dátumuk **egyetlen** `thumbindex` FILETIME-mal sem egyezik (sem az 1., sem a 2. mezővel, ±1,5 s). A közös másodpercek a közös létrehozást mutatják:

| katalógus | sorcsoport | dátum |
|---|---|---|
| `Picasa2` | `]screensaver`, `]updated`, `]history:email`, `]history:upload`, `]unknownface` | `2025-04-25 18:31:22` |
| `Picasa2` | `]star` | `2025-03-29 20:04:49` |
| `Picasa2` | `]search` | `2025-12-24 20:15:45` |
| `Picasa2-arcok` | `]star`, `]updated`, `]unknownface` | `2026-07-18 14:45:36` |
| `Picasa2-arcok` | `]screensaver`, `]history:email`, `]history:upload` | `2026-08-17 23:33:36` |
| `Picasa2-arcok` | `]facealbum:109`-`]facealbum:117` | `2026-08-15 18:43:47`-`18:51:23`, többnyire soronként más másodperc (a `109` és a `110` közös) |
| `Picasa2-arcok` | `]search` | `2026-08-22 20:36:25` |

A `]facealbum:N` sorok többnyire külön másodpercet viselnek: a személyek elnevezésének pillanatait. A `]updated` bélyege nem mozog a frissítésekkel: mindhárom katalógusban a vele együtt létrejött sorokéval azonos.

**A felhasználói albumsor** (a nagy katalógusban 17 fájlnév nélküli `]album:` sor): 16 dátuma egyezik valamely kép 1. FILETIME-jával, 9 a 2.-ával. A dátum tehát **tartalmi** (a tagok 1. mezőjének minimuma, a `0x00441ac0` útja), nem létrehozási bélyeg; a véletlen egyezés valószínűsége soronként nagyságrendileg 0,001 (egyenletes eloszlást feltételezve). Hogy az **üresen létrehozott, utóbb feltöltött** albumnál melyik hívó számolja ki először a dátumot, nincs meg: a `0x004aa9f0` kapuja a felhasználói albumot kihagyja (`0x004aac5e`-`0x004aad84`: a `[esp+0x15]` jelző a nem virtuális albumra 1, ilyenkor a `0x004aad7f` ugrása (`jne 0x4aae3f`) a dátum vizsgálata nélkül az állapotátmenet 0 → 1 lépéséhez vezet, `0x004aae3f`-`0x004aae49`; a 2-es állapotról a nézetlekérés sikere dönt, 38.2.190 §2), a `0x00441ac0` többi hívója mappára és leíróra áll.

**Mit jelent ez látható viselkedésként.**

- A `Recently Updated` (és a többi virtuális sor) kártyája az Időrendben a **sor létrehozásának idején** áll, nem a tagok képidején, és (az adat szerint) nem mozog frissítéskor. Frissen létrehozott katalógusban ez a jelenlegi hónap, tehát a kártya a rendezett lista (jobb) végén áll, "<hónap> <év>" felirattal. A Colab-felvételen ez látszik: `Recently Updated, November 2026` (job-665, `kepernyo__29.png`, 38.2.240), miközben a tagjai 2009-2019 közti mappák képei, és a dátumvonal jobb vége `November 2026`.
- Régebbi katalógusban a bélyeg a katalógus (vagy a sor) létrehozásának ideje: a `Picasa2` mintán `2025-04-25`, tehát a kártya a 2025. áprilisi gyűjtemények között áll, a későbbi (például 2025. decemberi) gyűjtemények **előtt**.
- A felhasználói album kártyája a tagjai legkorábbi képidején áll, és az automatikus úton rögzített; a mappakártyáé az első beíráskor számolt legkorábbi képidő (38.2.190 §5), vagy az ini `date=` értéke.

##### §5 A korábbi gépi jelentés pontjainak ellenőrzése

| A jelentés állítása | Ítélet | Indok |
|---|---|---|
| 1.1: a `0x004ada80` `param_1 == 0` ágán `fldz` + `0x00443c00` adja az új sor dátumát: `0,0` | **igaz** | `0x004adeeb`-`0x004adefc`, `0x00443c34`-`0x00443c41` (a hívó is ellenőrizte). Pontosítás: ez csak a nyers kezdőérték; a végleges dátumot a `0x0055d320` írja (§1/4) |
| 1.2: a `0x00441ed0` sem felhasználói albumot, sem virtuális sort nem dolgoz fel | **igaz, pontosítva** | a mappasort írja (`date=` vagy `0,0`), de csak sor-létrehozáskor; újraolvasáskor nem (§1/5). Az "ini-szinkron mindig beírja" nem igaz |
| 1.3 (1)-(2): a `0x004aa9f0` a `0,0` dátumra a `0x00441ac0`-t hívja, és e nélkül a sor nem jut 2-es állapotba | **részben téves** | a dátumkapu csak a mappa- és a virtuális sorra áll; a felhasználói album kihagyja, és üresen is 2-es állapotot kap (38.2.190 §2; `0x004aac5e`-`0x004aad84`) |
| 1.3 (3): a `0x00441760` a legkisebb "fájl- vagy felvételi" időt veszi | **pontosítva** | a rekord 1. FILETIME-ja: metaadat-dátum, tartaléka a beolvasáskori fájlidő (§2) |
| 1.3 (3): üres gyűjteménynél `-1`, ezért "az üres albumból soha nem lesz kártya" | **a `-1` igaz, a következtetés téves** | `-1`: `0x004417b9`, `0x00441875`. Az üres felhasználói albumot nem a dátum tartja ki, hanem a `0x007fc7c0` kártyaépítésének megszakadása (38.2.210 §3) |
| 1.3 (4): a dátum az első beíráskor rögzül, később nem módosul | **igaz az automatikus útra** | `0x00441ac0` kapuja; a többi író és kivétel: §3 |
| 1.3 (5): a virtuális sorok adatbázis-időbélyeget kapnak (`0x004abe70` → `0x004ad220`) | **igaz az eredményre, az író a jelentésben kimondatlan** | a leíró-konstruktor pillanatnyi ideje (§1/4, §1/6) |
| 2: a `Recently Updated` a legfrissebb gyűjtemények között áll, akkor is, ha a képei régiek | **igaz a bélyeg szerinti helyre** | a Colab `November 2026`; de a bélyeg a létrehozás ideje, nem "frissítés" |
| 3.1: a PicasaPy élőben számol, az eredeti tárolt dátumot használ | **igaz** | §6 |
| 3.2: EXIF nélküli képeknél a PicasaPy `date = None` | **igaz** | `_exif_date`; az eredeti a beolvasáskori fájlidőt használja (§2) |
| 3.3: a PicasaPy a `Recently Updated` kártyát a tagok `min(taken_at)` értékével látja el | **igaz az `origin/main` 1.0.110-re** | a jelentés sorszámai (`244-260`, `378-392`, `381-390`) nem pontosak; a helyek: lent. A kutatóág munkafája (`research/6532-claude`, a `main` mögött) még nem tartalmazza a kártyát |
| "`albums.ini` sztring nem létezik" | nem vizsgáltam | a kérdéshez nem kell |

##### §6 Összevetés a PicasaPy-val (`origin/main` 1.0.110, `src/picasapy/app/timeline_controller.py`)

| # | Eredeti | PicasaPy | Fok |
|---|---|---|---|
| 1 | EXIF nélküli kép dátuma: az 1. FILETIME, tartalék a beolvasáskori fájlidő (§2) | `_exif_date` csak a `taken_at`-et használja (`:396-404`), a lista `date=None`-nál a végére kerül (`:314-319`), `sliderPosition = 1,0` felirat nélkül (`:335`) | **igazolt eltérés** |
| 2 | A beírt dátum az automatikus úton rögzített, a tagok változása nem mozgatja (§3) | `_append_collection` minden újratöltéskor újraszámolja a látható tagok minimumát (`:367-394`) | **igazolt** (automatikus út, törlés és hozzáadás); **feltételes**: az üresen létrehozott, utóbb feltöltött album első beírása (§4) |
| 3 | Virtuális sor: a létrehozás bélyege (§4) | `AlbumRecord(token=RECENT_ALBUM_TOKEN, ..., date=None)` (`:248-253`), a kártya dátuma a tagok `min(taken_at)`-je (`:390`) | **igazolt a szabály** (nem tartalmi); **feltételes az érték** PicasaPy-ban |
| 4 | Albumsor: a tárolt `albumdata_date`; az ini-ből betöltött albumnál valószínűleg az ini értéke | élő minimum; az `AlbumRecord.date` (`index/albums.py:28-33`) megvan, az Időrend nem használja | **igazolt** a tárolt jelleg; **feltételes**: az ini `[.album:token] date=` mint elsődleges forrás (az olvasó nincs azonosítva) |
| 5 | A mappakártya dátuma a `folders.date` | élő minimum (`:367-394`) | **igazolt** (38.2.190 §5), a javaslat ott áll (§6/1); itt nem ismétlem |

**Nem javasolt megvalósításra (feltételes):** a virtuális kártya dátumának konkrét értéke PicasaPy-ban; az ini `[.album:] date=` elsőbbsége; az üresen létrehozott album első beírása; a `0,0`-ra állító jelző szerepe a Tulajdonságok ablakban.

##### Cáfoló kísérletek és amit kizártam

- **"A `0x00441760` a fájlidőt (a 2. mezőt) veszi."** Cáfolt: a `+0xc/+0x10` szavakat a ciklus nem olvassa (`0x00441988`-`0x004419ee`); a nagy katalógusban 44,0% az 86,1% ellen. A kis katalógusok 2. mezős találatai az `\export\` mappák, ahol az 1. mező a számoláskor még a fájlidő volt (§2).
- **"A `0x00441ed0` minden újraolvasáskor `0,0`-ra állítja a dátumot, és az újraszámolódik."** Cáfolt: a dátumírás a 3. argumentumhoz kötött (`0x004433f1`), a betöltő `0`-t ad (`0x0047c72e`).
- **"A virtuális sorok dátuma tartalmi (a tagok minimuma)."** Cáfolt: 40 sorból 0 egyezik képidővel; a vele együtt létrejött sorok azonos másodpercet viselnek.
- **"A felhasználói album a `0,0` dátum miatt nem jut 2-es állapotba."** Cáfolt: a `0x004aa9f0` kapuja a nem virtuális albumot kihagyja (`0x004aac5e`-`0x004aad84`).
- **"Az album-létrehozó kódban nincs dátumírás"** (38.2.210 §5): helyesbítve (§1 vége).
- **"A `Recently Updated` bélyege frissítéskor megújul."** Nincs rá bizonyíték: a három katalógusban a `]updated` bélyege a vele együtt létrejött sorokéval azonos, tehát a létrehozás ideje. Közvetlen felvétel (kép frissítése után) nincs.
- **Nem állítom:** a `0x008496c0` párbeszéd belsejét, a `+0x30` jelzőt `1`-re állító kódot (a 19 átvizsgált függvényben immediate-írás nincs, csak a `0x006dc0ef` nullázás), az ini `[.album:]` szakasz `date=` olvasóját, a `0x00452305` és a `0x0055822a` hívások szerepét.

##### Nyitott kérdések mérlege

Nyitott kérdések: 3 nyílt · 4 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 "csak nyitva"

| Kérdés | Állapot | Mi kell hozzá |
|---|---|---|
| Az album- és a virtuális sor dátumának kezdeti írója | **LEZÁRVA** (§1, §4) | |
| Melyik időbélyeget veszi a `0x00441760` | **LEZÁRVA** (§2) | |
| Rögzítettség, más írók, átnevezés és törlés | **LEZÁRVA** (§3; a törlés negatív, erős fokkal) | |
| A virtuális sor dátuma és látható helye | **LEZÁRVA** (§4) | |
| A felhasználói albumsor tartalmi dátumát kiszámoló hívó üresen létrehozott, utóbb feltöltött albumnál | **NYÍLT** | Ghidra-kör kell: `0x008496c0` és `0x00849dc0` (a leíró `+0x30` jelzőjét `1`-re állító kód és az `autodate` ág), `0x005ea770` és `0x005e8570` (`CThumbUI::albumname`, a hozzáadás parancsa), `0x004b9ee3` (Új album) |
| Az ini `[.album:token]` szakasz `date=` olvasója és szerepe a betöltött albumsor dátumában | **NYÍLT** | Ghidra-kör kell: `0x005608f0` (az album-ini betöltő, 3912 bájt) és `0x0055dbe0` (`property`/`value` diszpécser, a `date` összehasonlítás `0x0055df16`, `0x0055df3b`) |
| A `0x00452305` (`0x00451ff0`) és a `0x0055822a` (`0x00557ff0`) `[+0xc]` hívásának szerepe | **NYÍLT**, nem blokkoló | Ghidra-kör kell: `0x00451ff0` és `0x00557ff0` (hívója `0x005574b0`) |

##### Bizonyítottság

**Megerősített:** a `0x00441760` a leíró `+4/+8` szavát minimalizálja és a `+0xc/+0x10`-t nem olvassa (utasításolvasat); a `0x004edf60` a két mezőt külön másolja; az írók (`0x0040f980` mindkét mezőre, `0x004eeb10` csak az 1.-re) és a `0x00441ac0` `0,0`-kapuja; az ini-szinkron dátumírásának jelzőkapuja és a két hívási jelző (`0x004ade36` `1`, `0x0047c72e` `0`); a leíró-konstruktor pillanatnyi ideje és a `0x0055d320` dátumága; a `]search` soré; a 40 virtuális sor adatmérése. **Erős:** a törlés és az átnevezés dátumállósága (a pásztázott hívási alakokra negatív; az ablak belsejét nem olvastam); az export-mappák értelmezése (adat és utasításolvasat együtt, de más magyarázat, az ini `date=`, nem zárható ki); a felhasználói album tartalmi dátuma (16/17 egyezés). **Feltételes:** az ini `[.album:] date=` szerepe; a `Recently Updated` bélyegének változatlansága frissítéskor (felvétel nincs). **NINCS MEG:** a `+0x30` jelzőt bekapcsoló kód; az üresen létrehozott album első dátuma; a `0x00452305` és a `0x0055822a` szerepe.

**Módosított fájlok ebben a szakaszban.** Ez a 38.2.250 szakasz és a `picasa-idorend-viselkedes.md` A listájának dátum-qword tétele. Kódot, tesztet, eredeti binárist, felvételt vagy mérőadatot nem módosítottam; az ideiglenes mérőszkriptek és kimenetek a `$SCRATCH/6532g` mappából törölve.

##### Megvalósítási javaslat

Csak a binárisból igazolt eltérések; kódot nem módosítottam. A helyek az `origin/main` 1.0.110 szerintiek.

| # | Igazolt eltérés | Kódhely | Javaslat | Tesztötlet |
|---|---|---|---|---|
| 1 | EXIF nélküli kép dátuma (§2, §6/1) | `app/timeline_controller.py:280-286` (`all_dates`), `:367-394` (`_append_collection`), `:396-404` (`_exif_date`); kész függvény: `index/photo_date.py:13-46` (`photo_date`) | `_exif_date` helyett `photo_date(record)`: `taken_at`, tartaléka a befagyasztott fájlidő (a #6807 időzóna-kezelését megtartva); a dátumsáv `first_date` és `last_date` értékét ugyanebből | csupa EXIF nélküli (`taken_at=None`, `first_seen_mtime_ns` 2015-05-10) mappa 2014-es és 2016-os mappa mellett: a kártya a kettő között áll, `dateLabel` "May 2015", `sliderPosition` nem `1,0` |
| 2 | A virtuális sor dátuma nem tartalmi (§4, §6/3) | `app/timeline_controller.py:244-262` (`recent_album`, `date=None`), `:390` | a virtuális kártyára külön ág: dátuma a sor rögzített bélyege, nem a tagok `min`-je; **az érték (az index létrehozási ideje, importált db3-nál az `albumdata_date`) termékdöntés**, a binárisból csak az dől el, hogy nem tartalmi | `Recently Updated` tagjai 2005-ös `taken_at`-tal, bélyeg 2026-11: a kártya a rendezett lista végén áll, `dateLabel` a bélyeg hónapja, nem 2005 |
| 3 | A beírt albumdátum rögzített (§3, §6/2) | `app/timeline_controller.py:367-394` (albumág); az index új mezője a `#2486` mintájára (`index/schema.py:375-401`, `index/sync_photos.py:202-240`) | az albumkártya dátuma az első nem üres tagságnál rögzül (a tagok `photo_date`-minimuma), és tag hozzáadására vagy törlésére nem változik | 2020-as képekkel létrehozott album: kártya 2020; utóbb hozzáadott 2010-es kép után a kártya marad 2020 (a mai kód 2010-re ugrik); a 2020-as kép törlése után is marad |

### 38.2.260 Az Időrendből indított lejátszás időköze és átmenetei: a 08a mérés (#6532)

**Mérés:** Colab job-681 (`08a`, a job-680 sémahiba miatt újra), `video__04.mp4`: 1280x1024, 15 kép/mp, 675 kocka. Lépéssor: Időrend, két `Right`, `space` (szünetelő vetítés), `space` (lejátszás), 20 s, `space` (megállít), `Escape`.

| Állítás | Érték | Forrás |
|---|---|---|
| A második Space után a fotóváltások időköze | 45-46 kocka = 3,0-3,07 s (a váltások kezdete: kb. 493, 539, 585, 630. kocka) | mérés: képkockánkénti eltérés a felirat-területen, két független kiértékelés |
| A szünetelő nézetből a lejátszásba lépés | 24 kockás (1,6 s) felúszás a 447-470. kockán | mérés (két kiértékelés egyezik) |
| A fotók közti átmenet | áttűnés, az 5-95% közötti szakasz 11-12 kocka (kb. 0,75-0,8 s), a teljes áttűnés kb. 14-15 kocka (kb. 1,0 s) | mérés: lineáris keverési arány illesztése a 540-550., 585-596., 631-642. kockán |
| A harmadik Space megállít | a `kepernyo__17.png` és a `kepernyo__18.png` (2 s különbség) pixelre azonos | mérés |

**Összevetés a PicasaPy-val:** a 3 s-os időköz egyezik (`SlideshowTiming`, alapérték 3). Az áttűnés hossza **eltér**: nálunk `slideshowTransitionMs`, alapérték 700 ms, legfeljebb 500 ms-ra szorítva (`controller_slideshow_mixin.py`), az eredetiben kb. 1,0 s. Az eredeti átmenetidő-állandójának bináris címe még **NINCS MEG**; ennek feltárása külön kutatási jegy, a megvalósítás csak utána.
