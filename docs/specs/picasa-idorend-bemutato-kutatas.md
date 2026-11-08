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
  A közvetlen utasításolvasat szerint a dátumvonal két végén a qshow rekordtömb **0. és N-1. rekordjának** hónap-éve áll; a friss, független ellenőrző kör ezt nem erősítette meg. A rekordforrás pontosítása és a könyvtár egészével való viszonya a 38.2.102-ben feltételesként szerepel. A videón `May 2009` és `November 2026` látható. Bal felirat: jobbra zárva `track_left - 8`, `y = track_bottom - 3`; jobb felirat: balra zárva `track_right + 8`, `y = track_bottom - 3`. Szín: fekete, alfa `floor(floor(p · 127 / 256) · p / 256)`. Azt, hogy ezek a teljes könyvtár időhatárai-e, a videó önmagában nem dönti el.

**5. Sebességcsillapítás és megállási fókuszválasztás (`0x007fc010`, `0x007fd8c0`).**

- A sebesség csillapítása: `V = V · 0.95` (f64 `0x00cf40b0`) lépésenként (`0x007fc010:352`).
- A sáv megállt, ha `|V| ≤ S · 0.01 = 0.04999999888241291 · 0.01 = 0.0004999999888241291` (f64 `S@0x00cf4e30`, `0x00cf40b8 = 0.01`) és nincs futó animációs szakasz (`0x007fd8c0:1298`).
- Megálláskor a fókuszgyűjtemény az a rekord, amelynek `X` koordinátája legközelebb esik a `0.666`-hoz (f64 `0x00cf4860`); ennek indexe kerül a `[this+0x510]`-be, és ez indítja a `0x008018a0` gyűjteményváltást, jobb felső feliratcserét és háttér-átúsztatást.

**Összevetés a PicasaPy-jal.**

| Eredeti Picasa (binárisból igazolt) | Jelenlegi PicasaPy | Teendő |
|---|---|---|
| A kártya Z-mélységének alfája: `u = max(0, (1/Z - 1)/9)`, `fade = pow(u, 1.5)`, `alfa = round((1 - fade) · 256)` (`0x007fc010`, `0x005568e0`). | A `timeline_motion.py:96-97` pontosan ezt a képletet tartalmazza (`card_alpha`). | A matematikai modell megegyezik; a QML-ben ellenőrizni, hogy a kártyák rétege ezt az alfát kapja-e meg. |
| Láthatósági szűrő: `Z > 0.1` (`0x007fc010:366`, `0x00c7dd30`). | A `timeline_motion.py:28, 122` `VISIBLE_WIDTH = 0.1` küszöböt használ. | Megegyezik. |
| Kötegen belüli kártyák véletlen szórása: `dx, dy` a `[-0.075, +0.075]` tartományban (`0x008014d0`, `0x00cf3fd0`). | A `TimelinePanel.qml:261-264` determinisztikus, rögzített eltolást használ: `x: index * 4 * depthScale`, `y: -index * 3 * depthScale`, `rotation: -7 / +5`. | A rögzített szorzók helyett a bináris véletlen szórásmodelljét átvezetni a kártyák elrendezésébe. |
| Jobb felső feliratok: név `y = 130`, hónap-év `y = 158`, jobbra zárt `x = W - 90 - width`, 1 px fekete árnyék `(x+1, y+1)` (`0x007fee70`). | A `TimelinePanel.qml:342-371` `y: 108` és `y: 143`, `width: 180`, `x: panel.width - 270`, `style: Text.Outline`. | A feliratok Y koordinátáit és margóját a bináris pontos koordinátáira (`130`, `158`) igazítani, az outline helyett 1 px árnyékot alkalmazni. |
| 10 vezetőpont köbös Bézier íve: `P0 = (A-16, B)`, `P3 = (kártya_közép, kártya_fent - 20)`, `P1 = P0 + (0, 50)`, `P2 = P3 - (0, 50)` (`0x007fee70`). | A `TimelinePanel.qml:133-140` Canvas íve kézzel hangolt konstansokat használ (`startY + 42`, `endY - 48`, `control1X + 3`, `control2X + 38` stb.). | A Canvas `dotArcPoints` kontrollpontjait a bináris pontos képletére (`P1.y = P0.y + 50`, `P2.y = P3.y - 50`, `P3.y = firstPhoto.y - 20`) frissíteni. |
| A dátumskála két széle a qshow `0xf8` bájtos rekordtömbjének első és utolsó rekordjához fordul: a tömb címe `[this+0x3a8]`, a rekordszám `[this+0x3ac] >> 1`; a dátumlekérés a `CThumbDB+0x48` vtable `+0x20` slotján történik (`0x007ff476`-`0x007ff496`, `0x007ff4b8`-`0x007ff4f3`). A fókuszválasztó külön kiválasztja a `0x00cf4860`-hoz legközelebbi X koordinátájú rekordot, majd annak első dwordját adja vissza (`0x007fd8c0`-`0x007fd97a`). | A `timeline_controller.py:201-209,273-274` minden gyűjteményhez ugyanazt a teljes `records` halmazon számított minimum- és maximum-EXIF-dátum címkéjét adja; a `TimelinePanel.qml:553,645` az aktuális gyűjtemény objektumából olvassa e globális mezőket. | Az eredeti lista-végpontok és a PicasaPy globális dátumhatárai közötti tényleges egyezés vagy eltérés nincs megmérve. A qshow végpontrekordok és a PicasaPy dátumhalmazának futásidejű összevetése kell; a korábbi „fókuszgyűjtemény első/utolsó fotója” eltérésállítás téves volt. |
| Sebességcsillapítás: `V = V · 0.95`, megállási küszöb `|V| ≤ 0.04999999888241291 · 0.01 = 0.0004999999888241291`, a legközelebbi `X = 0.666` célú kártya kap fókuszt (`0x007fc010`, `0x007fd8c0`, `0x00cf40b0`, `0x00cf40b8`, `0x00cf4860`). | A `TimelineView.qml:143,367-371` hívásonként `0.95`-tel csökkenti a sebességet és a `CARD_STEP · 0.01` küszöbnél állítja meg; a `timeline_motion.py:26-28,141-159` ugyanezt a lépésközt, küszöböt és `FOCUS_X = 0.666` célt használja, a `finishCarouselMotion()` ezt a fókuszindexet választja (`TimelineView.qml:212-230`). | A forrásszintű csillapítási szorzó, küszöb és fókuszcél megfelel az eredetinek. Az eredeti és a PicasaPy frissítési ütemének, illetve a tényleges megállási képkockának az összehasonlítása még hiányzik; ebből most nem következik kódmódosítás. |

**Bizonyítottsági fok.** A kártyapályára, a Z-szűrőre és az átlátszóságra vonatkozó állítások, valamint a köteg-szórás és LOD a felsorolt bináris és Ghidra-források alapján megerősítettek. A feliratok elhelyezése és a vezetőpont-görbe képlete a közvetlen utasításolvasattal alátámasztott; a végfeliratok lista-végpontjainak értelmezése feltételes, mert a független, második ellenőrző kör nem tudta kiolvasni a célfüggvény utasításait. A PicasaPy globális dátumcímkéi és az eredeti qshow-végpontok tényleges egyezése/eltérése nyitott.
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
| A qshow dátumvonalának két felirata a saját `+0x3a8` rekordlistájának első és utolsó rekordjából kap hónap-évet (`0x007fee70`, `0x007ff476`-`0x007ff506`); a job-373 három vizsgált csoportja alatt a feliratok azonosak. | A `timeline_controller.py:201-209` a `_collections_to_qml` hívásnak átadott `records` dátumai közül egyszer számít minimumot és maximumot, majd ezeket minden gyűjtemény rekordjához rendeli (`:273-274`). A `TimelinePanel.qml:545-554,640-646` az aktuális gyűjtemény objektumáról olvassa ki a két címkét. | A két megjelenítési mód gyűjteményváltás közbeni viselkedése egyezik, de a PicasaPy `records` készletének és a Picasa qshow `+0x3a8` rekordlistájának tényleges azonossága nincs mérve. A rekordlisták futásidejű azonosítása előtt e részből nem következik dátumhatár-javítás. |

**A két út és bizonyítottsági fok.** A út: a friss utasításolvasat a bal/jobb feliratot az első/utolsó qshow-rekordhoz köti. B út: a job-373 három, különböző fókuszgyűjteményt mutató képkockáján a végfeliratok változatlanok. A utak egyeznek abban a szűk következtetésben, hogy a mért dátumvonal a fókuszgyűjtemény dátumpárját nem követi. A qshow-lista teljes katalógushoz való viszonya és a PicasaPy `records` készletével való azonossága továbbra is **nyitott**; a `0x007fee70` Ghidra-kimenet ugyanennek a függvénynek a másik reprezentációja, ezért arra nem támaszkodom második független útként.

**Cáfoló kísérlet.** Azt a feltevést próbáltam cáfolni, hogy a dátumvonal végei az aktuális gyűjtemény legkorábbi és legkésőbbi dátumát követik. A `n=150`, `n=300` és `n=420` képkockákon a fókuszfelirat 2009-ről 2014-re, majd 2019-re változik, a két végfelirat viszont mindhárom képen ugyanaz. Ez a feltevést a vizsgált három állapotra cáfolja. A három képkocka ugyanabból az egy felvételből származik; a vizsgált menet egészére vagy a teljes könyvtárra nem általánosítom.

**Nyitott.** A qshow `[this+0x3a8]` rekordlistájának tagjai, teljessége és a PicasaPy-ba átadott `records` halmazzal való azonossága **NINCS MEG**. Megszerzéséhez egy azonos Picasa-futásban rögzíteni kell a qshow rekordlista azonosítóit, a fókuszgyűjteményt és a két végfelirat dátumkulcsát, majd ezeket a PicasaPy azonos mappakészletből előállított `records` dátumaihoz hasonlítani. A helyi böngészőben nem volt Colab-fül; a helyi Colab-indító GitHub API-t igényel, ezért új futást ebben a körben nem indítottam.

#### 38.2.104 A job-446 képkockahatárai és a leütés-hozzárendelés (#6532, 2026-11-08)

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
