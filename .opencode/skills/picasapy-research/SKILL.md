---
name: picasapy-research
description: PicasaPy bináris-kutatás indítása — vegyél elő egy nyitott vagy kérdéses viselkedést az eredeti Picasából, és fejtsd vissza bizonyítékkal (index → dekompiláció → mérés → docs/specs + jegy). Akkor hívd, ha a felhasználó kutatást kér („kutasd”, „fejtsd vissza”, „hogyan csinálja az eredeti”), vagy ha ezt a skillt nevesíti. Fejlesztéshez (jegy végigvitele kódig) a `picasapy-dev` való.
---

# PicasaPy bináris-kutatás (picasapy-research)

Egy hívás, ami elindítja a rendes kutatói kört: **nyitott kérdés → bizonyíték
→ dokumentált spec**. A cél nem kód, hanem **visszakereshető tudás**.

**Ez a fájl NEM tartalmazza a módszertant.** Az eszközkatalógus a
`docs/specs/binaris-regeszet-modszertan.md`-ben él (mit hoz ki egy szerszám,
mikor kell érte nyúlni, és mit NEM lát), a Ghidra-futtatás mechanikája pedig
a `picasa-x86-research` skillben. Itt csak a sorrend van.

Ha ez a kettő szétcsúszik, a `docs/specs/` az igazság.

## 0. Ellenőrizd, hogy nem vakon dolgozol

A privát agent-kontextusnak (`picasapy-agent`) megvan kell lennie — a
session-start hook klónozza. Olvasd el a `PROTOKOLL.md`-t (a repóhatár, a
jegykezelés és a hatókör-szabály a kutatásra is érvényes), a
`memory/00-index.md`-t és a `memory/tanulsagok.md`-t.

## 1. Kérdésválasztás

**Először a `docs/specs/00-index.md`-t nyisd meg.** Az elején egy
**kézzel karbantartott lista** áll a valóban nyitott kérdésekről, laponként
csoportosítva. Innen válassz — a teljes mappa végiggrepelése fölösleges.

⚠️ **Ne a `Nyitva` szavak számából indulj ki.** Egy 2026-08-16-i
átvilágítás szerint a szó **kétharmada hivatkozás** egy máshol már
megválaszolt pontra (a `filterdesc-registry.md` hat találatából **nulla**
volt valódi nyitott kérdés). Ezért van az indexben kérdés-lista és nem
számláló.

Honnan jönnek a nyitott kérdések, ebben a sorrendben:

1. **`ready` címkés kutatási jegyek** (`list_issues`) — a foglalás-ellenőrzés
   a `PROTOKOLL.md` szerint itt is kötelező;
2. `docs/specs/00-index.md` „Hol van nyitott kérdés" táblája;
3. `docs/research-plan.md` „nyitott" tételei;
4. a kiválasztott lapon a konkrét „Nyitva" / „dekódolatlan" /
   „uncalibrated" jelölés;
5. `docs/specs/feature-map.md` fehér foltjai.

Egy körben **egy JELENSÉG** — és azt végig kell vinni.

⛔ **A leggyakoribb hiba: félbehagyás jegynyitással.** Ez a szabály korábban
így szólt: „egy körben egy kérdés, ha másikba botlasz, jegyet nyiss rá" —
és ezzel **szabályos kiszállást adott** abban a pillanatban, amikor a kör meg
tudta nevezni a következő részkérdést. A tulajdonos vette észre
(2026-08-20): *„ha világosan meg tudod fogalmazni, mi a nyitott kérdés,
akkor végig kéne rajta menned."* Igaza van.

**Válaszd szét a kettőt:**

| amibe belebotlasz | mit tegyél |
|---|---|
| **ugyanannak a jelenségnek a következő részkérdése** (ugyanaz a panel, ablak, szűrő, formátum) | **MENJ TOVÁBB** — ez ugyanaz a kör |
| **másik téma** (másik panel, másik funkció, egy közben talált hiba a mi kódunkban) | jegyet nyiss rá, és ne térj el |

**Kiszállni CSAK akkor szabad, ha az olcsó bizonyítéklánc KIMERÜLT.** A lánc:

```
docs/specs + referencia/  →  szövegtár (stringres)  →  sztring-xref
  →  respack.yt (geometria!)  →  xrefs (hívási lánc)  →  imports
  →  [innentől drága: célzott dekompiláció]
```

Amíg a láncból bármelyik lépés **nincs kipróbálva**, a kérdés nincs
átadható állapotban. Ha átadod, a jegy **sorolja fel, mit próbáltál** — nem
elég azt leírni, mi maradt nyitva.

**Bizonyíték, hogy kell ez a szabály (2026-08-20, lebegő értesítősáv):** a kör
öt kérdést hagyott nyitva, köztük a geometriát — „a `respack.yt` nincs meg a
kutatási anyagban" indoklással. A fájl **megvolt** a repóban, és amikor a
tulajdonos ráparancsolt, **percek alatt** kiadta a teljes geometriát (247×45
cella, három vezérlő, folyamatjelző) — sőt olyat is, amit a szövegek elvileg
sem adhattak volna meg. Két lánc-lépés kimaradt: a `respack.yt` és az `xrefs`.

## 1/b ⛔ A KÖR NEM ZÁRHATÓ SAJÁT NYITOTT KÉRDÉSSEL

> **A kanonikus elv a `PROTOKOLL.md` „Lelet-elszámolás" szakaszában van**
> (*semmi nem maradhat névtelenül nyitva, a kör végén számokkal el kell
> számolni*). Ez a szakasz annak a **kutatási állapotkészlete** — a
> review-köröké ugyanott, külön táblában. A két készlet szándékosan eltér;
> az elv egy, és csak egy helyen van kimondva.

Az 1. szakasz szabálya („ne szállj ki, amíg az olcsó lánc nem merült ki")
**nem fogott meg**, mert a 4. szakasz jegy-sablonjában ott áll egy „Ami
NYITVA marad" mező — és ez **szabályos kimenetté tette a félbehagyást**.
A kör leírta a kérdést, kipipálta magát, és kész.

A tulajdonos 2026-08-21-én kimondta: *„Minden nyitott kérdést kötelező
kivizsgálni."* Ez tehát nem ajánlás.

### A kulcskülönbség: ÖRÖKÖLT vs. SAJÁT kérdés

| | mit szabad vele |
|---|---|
| **ÖRÖKÖLT** — a kör előtt is nyitva volt (más lapon, más körből) | maradhat nyitva; a munkasorba kerül |
| **SAJÁT** — EBBEN a körben fogalmaztad meg először | **NEM maradhat nyitva.** Le kell zárni, vagy a három állapot egyikébe tenni |

**A három megengedett végállapot** — „egyszerűen nyitva" NINCS köztük:

| állapot | mikor | mit kell mellé írni |
|---|---|---|
| **LEZÁRVA** | megválaszoltad | a válasz + a bizonyíték címe |
| **BLOKKOLT** | gépi úton nem eldönthető | **mi kell hozzá, kitől** (képernyőkép, export, windowsos próba) + jegy `blocked` + `felhasználóra-vár` címkével |
| **HATÓKÖRÖN KÍVÜL** | tulajdonosi döntés vagy nyilvánvalóan nem építjük meg | **ki és mikor döntötte el** |

Ha egy saját kérdésed egyikbe sem fér bele, **a kör nincs kész — dolgozz
tovább rajta.**

### Az elszámolás KÖTELEZŐ, és SZÁMOKKAL

Minden kör záró összefoglalója tartalmazza ezt az egy sort:

```
Nyitott kérdések: N nyílt · M lezárva · K blokkolt · L hatókörön kívül · 0 „csak nyitva"
```

Ha az utolsó szám nem nulla, **a kör nem zárható.**

### Az örökölt kérdések sem tűnhetnek el

Ami örököltként nyitva marad, annak **be kell kerülnie a munkasorba**:
`picasapy-agent` → `memory/nyitott-kerdesek-sor.md`. A sor a feldolgozás
sorrendje; a `docs/specs/00-index.md` marad a hivatalos leltár. A kör
végén mondd meg, **hány tétel van a sorban** — így nem lehet úgy „kész"
egy kör, hogy közben a sor csendben nő.

### Miért nem volt ez eddig automatikus — a mechanizmus

Mert a kör „készségét" a **leadott termék** mérte (spec-lap + jegy), és a
nyitott kérdés a terméken BELÜL egy legitim rovat volt. Amíg a
befejezettség definíciója nem tartalmazza a kérdés-mérleget, a felsorolás
mindig olcsóbb, mint a kivizsgálás — és a kör a felsorolást választja.
**Ezért a definíció változott meg, nem a jószándék.**

## 2. A kutatói kör — OLCSÓ BIZONYÍTÉKKAL KEZDJ

```
meglévő index → string/xref → RTTI/vtable → célzott dekompiláció
  → mérés/golden-pár → docs/specs + jegy
```

**Soha ne kezdd dekompilációval.** A sorrend nem stílus kérdése: a legtöbb
kérdés az első két lépésben eldől, tört annyi költséggel.

> ⚠️ **De a felderítés SORRENDJE külön kérdés:** felületi elem kutatásánál
> a **működést** kell előbb felderíteni, nem a geometriát — ld. **2/b**.

1. **Meglévő anyag** — hátha már megvan:
   `referencia/dekompilalt*/` (korábbi Ghidra-körök nyers kimenete),
   `referencia/research-*.md`, `docs/specs/`.
2. **Bináris index** — `referencia/binary-index/picasa3-index.sqlite`
   (`functions`, `xrefs`, `string_xrefs`, `rtti`, `data_symbols`) és a
   `stringres-en-hu.tsv`. Egy elemnév vagy kulcs kikeresése, majd a rá
   hivatkozó függvények — ez adja meg, HOL keresd.
3. **Célzott dekompiláció** — csak konkrét címmel és konkrét kérdéssel,
   a `picasa-x86-research` skillel. Az EXE-t nem szabad commitolni,
   publikálni vagy jegyhez csatolni.
4. **Mérés** — ahol pixel- vagy paraméter-pontosság a tét, golden-pár kell
   (eredeti Picasa-export vs. a mi kimenetünk), nem szemre-egyezés.

## 2/b ⛔ A FELÜLET NEM A MŰKÖDÉS — kötelező visszafejtési sorrend

**Ez a skill legdrágább, ismétlődő hibája:** a kör kimerítően leírja, hogy
mi hol van a képernyőn, és **nem írja le, mi történik az ADATTAL**. A
tulajdonos több sessionben szóvá tette; 2026-08-21-én kimondottan is:
*„Mindig csak a kinézettel foglalkozol… a UX és a backend részletek nem
érdekelnek a kutatáskor."*

**Miért történik?** Mert a `respack.yt` és a `.tre` **olcsó, gyors és
lezárható**: fél óra alatt kijön 30 réteg pontos koordinátája, és a
táblázat késznek LÁTSZIK. A viselkedés viszont diszasszembly-olvasás, ami
lassabb és nem ad „kerek" táblázatot — ezért a figyelem magától a
geometria felé csúszik. A skill 2. szakaszának bizonyítéklánca ezt
felerősítette: benne a `respack.yt` mellett ott állt, hogy „**geometria!**".

### A javítás: a MŰKÖDÉST kell ELŐBB felderíteni

**Fordítsd meg a sorrendet.** Egy panel/dialógus kutatásánál a
geometria ELŐTT jöjjön:

```
1. MI AKTIVÁLJA?  MINDEN belépési pont: menütétel(ek), gyorsbillentyű,
                  gomb, helyi menü, dupla katt, fogd-és-vidd, automatikus
                  esemény (indulás, figyelő, időzítő). Egy parancsazonosító
                  TÖBB menüben is szerepelhet — ellenőrizd!
2. MIT INDÍT EL?  kifelé: másik párbeszéd, háttérszál, újraindexelés,
                  értesítés, böngésző, másik panel megnyitása
3. MIT ÍR?        fájl / registry / adatbázis-token a hívási gráfban
4. MIKOR?         azonnal · OK-ra · kilépéskor · háttérszálon
5. MI TÖRTÉNIK A MEGLÉVŐ ADATTAL?  törlődik · elrejtődik · újraolvasódik
6. MI FUT LE UTÁNA?  újraindexelés · folyamatjelző · értesítés
7. HIBAESET:      nincs jogosultság · leválasztott meghajtó · hiányzó fájl
8. HONNAN JÖN INDULÁSKOR az állapot?
--- és CSAK EZUTÁN ---
9. elrendezés, geometria, ikonok
```

**Az 1. és a 2. pont a legkönnyebben kifelejtett — és a legdrágább.** A
belépési pontok a menüépítő függvényben egy **parancsazonosító** köré
gyűlnek: keresd meg az azonosítót, és nézd meg, **hány** menüben szerepel.
Nálunk ez egyszer már megharapott (#936: a menüpont elsütötte a jelzést, és
az a semmibe ment; #1006: két hiányzó belépési pont), és a Mappakezelőnél
is: az `ID_TOOLS_INCLUDEEXCLUDEFOLDERS` **két menüben** ül („Fájl → Mappa
hozzáadása a Picasához…" és „Eszközök → Mappakezelő…"), nálunk az egyik
**halott placeholder**.

### A konkrét keresőrecept (percek, nem órák)

```sql
-- 1) a panel függvényeiből induló hívási gráf 2 szintje, és minden
--    fájlnév / registry-út / ]token, amit érintenek:
SELECT DISTINCT string, function_address FROM string_xrefs
WHERE string LIKE '%.txt' OR string LIKE '%.db'  OR string LIKE '%.ini'
   OR string LIKE '%.xml' OR string LIKE '%.pmp'
   OR string LIKE 'Preferences\%' OR string LIKE 'Software\%'
   OR string LIKE ']%';
```

majd a talált íróra: **milyen módban nyit** (`"w"` = teljes újraírás vs
`"a"`), **milyen formátumsztringgel** ír soronként (az előtagok — `+`, `-`
— itt derülnek ki), és **melyik tagváltozóból**.

> **A 2026-08-20-i Mappakezelő-kör erre pontos példa:** a 583 soros spec
> első kiadása a teljes geometriát tartalmazta, a működésből viszont
> semmit. Egy **10 perces** utólagos kör megtalálta a `watchedfolders.txt`,
> `frexcludefolders.txt` és `scanlist.txt` fájlokat, a `"%s\n"` / `"-%s\n"`
> / `"+%s\n"` háromféle sorformátumot, és **valódi mintafájlokat a saját
> repónkban** (`research/testdata/`). Ez volt a funkció fele — és majdnem
> kimaradt.

### ⛳ Átadási feltétel

**Egy panel/dialógus spec-lapja NEM teljes, amíg nincs benne egy
„Mit CSINÁL" szakasz**, ami megnevezi a megváltoztatott tárolót (fájl,
registry-kulcs, adatbázistábla), a **formátumát**, és az érvényesülés
pillanatát. Ha ez nincs meg, a lap fejlécébe kerüljön oda:
**„a működés NINCS feltárva, csak a felület"** — hogy a következő kör
tudja, hol tartunk.

**Keresd meg a saját adatunkban is:** a `research/testdata/` alatt valódi
Picasa-adatmappa van (`Picasa2/`, `Picasa2Albums/`, `db3/`). Mielőtt egy
formátumot a binárisból következtetnél, **nézd meg, van-e rá élő minta.**

## 3. Bizonyíték-fegyelem

- **Hivatkozás cím nélkül nem bizonyíték.** Minden állítás mellé
  visszakereshető cím (image base / RVA / fájloffset) vagy fájl+sor.
- **Mondd ki a bizalmi fokot**: megerősített / erős / feltételes / elvetett.
  A „feltételes" tisztességes válasz — a magabiztos találgatás nem az.
- **A negatív eredmény is eredmény.** Az elvetett hipotézist és azt, hogy MI
  döntötte el, ugyanúgy le kell írni — enélkül a következő kör újra
  végigjárja ugyanazt a zsákutcát.
- **A komment nem bizonyíték** — sem a miénk, sem egy korábbi köré.

## 4. Lezárás — a kutatás akkor kész, ha leírtad ÉS megválaszoltad

⚠️ **A leírás nem pótolja a választ.** Ez a szakasz az átadás formájáról
szól; attól, hogy egy kérdés szépen meg van fogalmazva a jegyben, még nincs
megválaszolva. A kiszállás feltétele az 1. szakaszban áll: a **kimerített
olcsó bizonyíteklánc**.

A kimenet **mindig** ez a kettő:

1. **`docs/specs/` frissítés** — a megfejtés a megfelelő lapon, a
   bizonyítékkal és a bizalmi fokkal. Új, nagyobb téma esetén új lap.
2. **Jegy-komment vagy új jegy** — mi derült ki, mi maradt nyitva, és mi
   ebből implementálható. Ha implementálható, az már a `picasapy-dev` dolga:
   **ez a skill nem ír terméki kódot.**

A kutatói jegy ugyanúgy a vállalóé a lezárásig, mint a fejlesztői
(`PROTOKOLL.md`, „A feladat-ciklus VÉGE").

### ⛳ A MÉRCE: egy friss fejlesztő CSAK a jegyből építsen helyeset

**Nem az a mérce, hogy TE érted.** A kör akkor kész, ha egy fejlesztői kör —
ami semmit nem tud erről a beszélgetésről — **kizárólag a jegyből** azt
építi meg, amit kell.

Hat követelmény; átadás előtt mindet nézd végig:

1. **Teljes elemlista, nem minta.** Ha egy panel geometriájáról van szó, mind
   a 201 eleme kerüljön ki, ne a legfeltűnőbb három.
2. **A MI oldalunkat is mérd ki.** Az eredeti leírása önmagában nem mondja
   meg, mit kell átírni — a jegyben „**eredeti / nálunk / teendő**" álljon.
3. **Válaszd szét a normatívat a tájékoztatótól**, és indokold, miért.
4. **Pipálható lista a végén**, ne próza.
5. **A kivételeket számszerűsítsd.** „Hét fül öt helyett" nem elég:
   39/39/40/39/40/39/40 = 276.
6. **Kontrollkérdés: „csak én értem a jegyet?"** Ha igen, még nincs kész.

### ⛔ A MEGFEJTETT MECHANIZMUS NEM DIAGNOSZTIZÁLT OK

**A két állítás külön bizonyítást igényel:**

- „**így működik az eredeti**" — ezt a bináris igazolja;
- „**ettől lesz jó a mi kimenetünk**" — ezt **csak mérés** igazolja.

A spec és a jegy **soha ne engedje**, hogy az olvasó a másodikat a
elsőből következtesse. Ha egy mechanizmust megfejtettél, de **nem
mérted le, hogy csökkenti-e a mért eltérést**, azt írd oda:

> *Megfejtve, de a mért eltérésre gyakorolt hatása NINCS mérve.*

**Bizonyíték, hogy kell ez a szabály (2026-08-18, #879):** a spec
helyesen írta le a `finetune2` hőmérséklet-ágát (feketetest-tábla + az
`autocolor` mátrixa), a rangsor pedig — külön — azt, hogy a `finetune2`
a legnagyobb tényleges hatású hiba (55,94 ΔE, 561 kép). A fejlesztő
jogosan kötötte össze a kettőt, megvalósította a hőmérsékletet, és
lemérte: az „alap" eset **bitre ugyanannyi maradt**, a jó „min" eset
pedig **1,12 → 2,86-ra romlott**. A hőmérséklet nem volt az ok. Fél nap
ment el rá, és csak azért nem került ki romlás javításként, mert a
fejlesztő **beépítés előtt mért**.

### ⛔ A KOMPOZÍCIÓT is írd le, ne csak a komponenseket

Ha egy szűrő vagy panel **több lépésből** áll, a spec mondja meg:

1. a lépések **sorrendjét**,
2. hogy melyik lépések **osztoznak egy menetben** (közös LUT, közös
   pufferbejárás), és melyik külön,
3. **hol történik kvantálás/vágás** (8 bit? 16 bit? hányszor?),
4. és ha ezek bármelyike **feltevés**, azt nyitott kérdésként.

**Komponensenként helyes megvalósítás is adhat rossz kompozitot.**

**Bizonyíték (ugyanaz a nap, #879):** a `finetune2` csúcsfény- és
árnyék-vezérlője az eredetiben **egyetlen 256 × uint16 LUT**, egyetlen
vágással (`0x0090c430` → `0x0090c1e0` + `0x0090be70`). Nálunk két külön
menet, **mindkettő 8 bitre vág**. Egy vezérlővel a kettő **bitre
azonos**, kettővel viszont **akár 217 szintet** téved. A spec a
komponenseket leírta, a kompozíciót nem — a mi kódunk docstringje még ki
is mondta, hogy a sorrend „dokumentált feltevés", és ez **sosem került
be nyitott kérdésként a specbe**.

**Ebből következik a tesztekre nézve is:** ha a mérőkészletben csak
**egy-vezérlős** esetek vannak, a zöld készlet a kompozit hibát **nem
fogja meg**. Átadás előtt nézd meg, van-e kompozit eset — ha nincs, az
önmagában jegy.

### ✅ Átadás előtti önellenőrzés — három kérdés

Mielőtt kiadsz egy specet vagy jegyet, válaszold meg magadnak:

1. **Mit csinál a fejlesztő holnap másképp?** Ha erre nincs egy
   mondatos válasz, a spec még leírás, nem átadás.
2. **Miből fogja tudni, hogy sikerült?** Ha nincs mérhető feltétel és
   nincs hozzá mérőanyag, mondd ki, hogy nincs — és nyiss rá jegyet.
3. **Mi az, amit NEM tudok, de a szöveg alapján tudni látszik?** Ezt írd
   le kifejezetten. A magabiztos hallgatás drágább, mint a bevallott
   hiány.

### ⚠️ A `docs/specs/` frissítése NEM helyettesíti a jegyet

A leggyakoribb csendes hiba: a spec megtelik bizonyítékkal, de a **jegy nem
kap kommentet** — a tudás megvan, a fejlesztés mégsem találja meg.
**Öt egymást követő kör csúszott el pontosan így** (2026-08-16), és a
felhasználó vette észre, nem a kör.

**Minden kör végén, kivétel nélkül:** a jegy kapjon kommentet a leletről és a
konkrét teendőről, vagy nyíljon rá új jegy. Ha a lelet egy MÁSIK, meglévő
jegyet is érint (pl. egy render-mérés a `#317`-be tartozik), **oda is írd
be** — a specbe írás önmagában nem átadás.

> A bizonyíték, amit senki nem talál meg, nem ér többet a hiányzó
> bizonyítéknál.

#### ⛔ A GYŰJTŐJEGY NEM ELÉG — ha a lelet önállóan megvalósítható, ÚJ JEGY kell

Ez a szabály második, élesebb fele, mert az első nem volt elég: a körök
**kommenteltek** ugyan, de **gyűjtőjegyekre** (`#317`, `#452`), és a
konkrét, önmagában megcsinálható munka ott elveszett.

**Új jegy kell, ha a lelet:**

- **hiba** a mi kódunkban (akkor is, ha egy mérés melléktermékeként bukkant elő);
- **hiányzó vezérlő, panel vagy funkció**, amit egy fejlesztő egy körben megcsinálhat;
- **mért geometria vagy viselkedés**, aminek ma más a megvalósítása;
- olyasmi, amire a „Kész, ha" listát **önállóan** meg lehet írni.

**Elég a komment a meglévő jegyen, ha a lelet:**

- egy már nyitott kérdés **megválaszolása** ugyanabban a jegyben;
- **negatív eredmény** („ezt nem kell megcsinálni");
- **helyesbítés** egy korábbi állításon.

Bizonyíték, hogy kell ez a szabály (2026-08-16): huszonöt kör után a
felhasználó kérdezett rá, és **négy lelet** maradt jegy nélkül vagy rossz
jegyen — köztük egy **valódi renderelési hiba** (a `radsat` ellipszist rajzol
kör helyett) és egy **teljes panel** specifikációja (importálás), ami csak
spec-lapként létezett.

#### A kör NEM ér véget a PR-ral

A kör akkor kész, ha **kimondtad, melyik jegybe került**. A záró
összefoglalóban körönként egy sor:

```
3. kör — a görgetősáv saját vezérlő → ÚJ JEGY #857
4. kör — a fiók váltása a Nézet menüből → komment #754
```

Ha egy sorba nem tudsz jegyszámot írni, **a kör nincs kész.**

#### Több körös menet végén: ellenőrző lista

Öt vagy több körnél a menet végén nézd végig:

```bash
gh issue list --state open --limit 100 --json number,title   --jq '.[]|"#\(.number) \(.title)"' | grep -i "<a témád kulcsszava>"
```

Minden körhöz legyen jegyszám. **A gyűjtőjegybe írt komment nem
számít**, ha a lelet önállóan megvalósítható.

### A jegy SABLONJA — ezt a hét szakaszt írd meg

Ne találd ki minden körben újra. A dev ezt a sorrendet várja:

```markdown
## MIT AD MA         — a MAI kódunk MÉRT állapota, EZ AZ ELSŐ SZAKASZ
## A lelet            — mi derült ki, 2–3 mondatban, emberi nyelven
## Bizonyíték         — cím (RVA/fájloffset) vagy fájl+sor MINDEN állításhoz
## Eredeti / nálunk / teendő   — TÁBLÁZAT, a mi tényleges értékeinkkel
## Kész, ha           — pipálható lista, MÉRHETŐ feltételekkel
## Bizonyítottsági fok — megerősített / erős / feltételes / elvetett
## Nyitott kérdések mérlege — MINDEN tétel LEZÁRVA / BLOKKOLT /
##   HATÓKÖRÖN KÍVÜL állapotban, indoklással; „csak nyitva" TILOS (1/b).
##   A sor: N nyílt · M lezárva · K blokkolt · L hatókörön kívül · 0 csak-nyitva
## Amit KIZÁRTAM      — a megdőlt hipotézisek, hogy ne járják újra
```

### ⛔ AZ ELSŐ LÉPÉS MINDIG: MÉRD FEL A MAI KÓDOT

A fejlesztői szál jelentette (2026-08-25): *„A felvett jegyek **felénél** a
mérés mást mondott, mint a jegy. A Képkupacról kiderült, hogy jó; egy
régió-adat, amit kerestünk, nem is létezik; egy »termékhibáról« kiderült,
hogy a teszt feltevése rossz."*

> **Minden jegy első szakasza: „MIT AD MA" — a mai kódunk MÉRT állapota.
> A jelentés első mondata is ez legyen.**

Az „eredeti / nálunk / teendő" tábla **„nálunk" oszlopa MÉRÉS**, nem
feltevés. Ha nem mérted, oda **„nem mérve"** kerül — soha nem „nincs".

**A három mozdulat, két perc:**

```bash
grep -rln "<fogalom EN>\|<fogalom HU>" src/ --include=*.py --include=*.qml
head -30 <talált fájl> ; grep -nE "^def |^class |^[A-Z_]+ *=" <fájl>
gh issue list --state all --search "<kulcsszó>" --limit 20   # <<< a leggyakrabban kihagyott
```

**A harmadik a legfontosabb:** a saját korábbi körünk már feltárhatta. Ha a
modul fejléce jegyszámot említ, **olvasd el azt a jegyet**, mielőtt „új
leletet" hirdetsz.

**Bizonyíték, hogy kell (2026-08-25, #1399):** a kör azt írta, hogy „nálunk
nem számolunk átlagszínt" és „a hat szín szerinti keresésből egy sincs".
A mérés: az `index/colors.py` épp `avgcolor`-t számol (0xAARRGGBB), a
`color/classify.py` **tíz** keresőtokent ismer magyar aliasokkal — és a
**#383 mindezt már lekutatta**. A valódi hiány **csak a menü-belépési pont**
volt. Ugyanabban a körben még három jegy „nálunk" oszlopa volt pontatlan.

**Miért csúszik el magától:** a bináris kutatása érdekes és kerek, a saját
kódunk felmérése unalmas grep. A jegy ettől késznek LÁTSZIK — a
bizonyíték-oszlop tele van címekkel —, miközben a fele hamis.

**A „Kész, ha" feltétele legyen a dev környezetében ELLENŐRIZHETŐ.** Ha
külső anyag kell hozzá (export, képernyőkép), azt **mondd ki**, és a jegy
kapjon `blocked` + `felhasználóra-vár` címkét a konkrét kéréssel — ne
maradjon teljesíthetetlen elfogadási feltétel.

### A jegy CÍME és CÍMKÉI

- **A cím a leletet nevezze meg, ne a kört.** Ha menet közben nő a hatókör,
  **nevezd át** (`gh issue edit <N> --title …`).
- **Címkék átadáskor:** `ready` (foglalás vissza), típus (`bug`/
  `enhancement`), prioritás (`P0`–`P4`), komponens (pl. `ui`).
- **Ha a felhasználó által LÁTOTT hiba:** `next-up` is, ÉS egy sor a
  rangsor-jegybe (**#484**) az indoklással. `ready` önmagában ~35 jegy
  közé süllyed — ott a dev nem fogja kiválasztani.
- **A foglalást add vissza:** `in-progress` le, `ready` fel. Lezárt jegyen
  soha ne maradjon `in-progress`.

### Karbantartás: a `00-index.md`-t UGYANABBAN a PR-ban vezesd át

A `docs/specs/00-index.md` a specifikációk tartalomjegyzéke. **Nem külön
kör frissíti** — aki hozzányúl egy spec-laphoz, ugyanabban a PR-ban hozza
rendbe az index sorát is:

| ha a kör… | akkor az indexben… |
|---|---|
| **új spec-lapot** hoz létre | egy sor a megfelelő témakör táblájába |
| **nyitott kérdést zár le** | a kérdés kikerül a listáról; ha a lapon nem marad több, a lap fejléce is |
| **új nyitott kérdést talál** | egy sor a lap listájába, **EGY MONDATBAN megfogalmazva** — a spec-lapra írt puszta „Nyitva" szó nem elég, mert a következő kör abból nem tudja, mit kellene megválaszolni |
| lapot **átnevez vagy összevon** | a hivatkozás javítása |

Gyanús helyek előkeresése (ellenőrzésre, **nem** karbantartásra):

```bash
grep -n 'Nyitva\|NYITOTT\|dekódolatlan\|uncalibrated' docs/specs/*.md \
  | grep -v '~~' | grep -v 'LEZÁRVA\|MEGVÁLASZOLVA\|MEGOLDVA\|MEGDŐLT'
```

Ha az index elavul, a következő kör rossz helyen fog ásni — ezért ez
ugyanolyan kötelező, mint a jegy-komment.

### Karbantartás: a megválaszolt jelölést a MÁSIK lapon is vedd le

Ha a kör megválaszol egy `Nyitva`/`dekódolatlan` jelölést, keresd meg a
**többi** lapon is, és vezesd át (áthúzás + mutató a válaszra). Egy
2026-08-16-i átvilágítás **nyolc** olyan jelölést talált, amit a saját
későbbi munkánk már megválaszolt — a bizonyíték megvolt, a jelölés mégis
zsákutcába küldött volna egy következő kört.

### ⛔ A `.tre` NEM adja meg az elrendezést — a `respack.yt` adja

**Ez a hiba két körben is megismétlődött**, és a felhasználónak kellett
képernyőképpel megcáfolnia (2026-08-16, #464).

A Picasa felületleíró nyelvében a `.tre` a **szülő-gyerek viszonyt és a
viselkedést** rögzíti. Ha egy elem sora csak ennyi:

```
editpanel/<gomb>: editpanel/tabpanel1
m_offsetLT
```

akkor a fájl a **helyét nem adja meg** — az `m_offsetLT` a szülő
bal-felső sarkához horgonyoz, eltolás nélkül. Tíz ilyen gomb **egymáson
ülne**. A tényleges koordináták a **`respack.yt` tervezővásznán** vannak.

**Sorrendre, pozícióra, méretre SOHA ne következtess a `.tre`
deklarációs sorrendjéből.** A lekérdezés másodpercekbe telik:

```bash
python3 tools/picasa/respack.py list <respack.yt> | grep <panelnév>
```

majd a 13 bájtos fejléc `int16 x0,y0,x1,y1` mezőiből olvasd ki a rácsot.
(A `picasa-respack-format.md` figyelmeztetése — „az abszolút pozíciók
tervezővászon-koordináták" — a **`.tre`-vel való ütközésre** vonatkozik,
nem arra, hogy a rács-SORREND bizonytalan volna: az egy panelen belüli
relatív sorrend és osztás megbízható.)

### ⛔ Ha a felhasználó képernyőképet ad, AZ a bizonyíték

A tulajdonos futó, valódi Picasa 3-ból készít képernyőképet. Ha az
ellentmond a mi olvasatunknak, **a mi olvasatunk a hibás** — a
következtetés vagy a forrás rossz, nem a kép.

Ilyenkor a teendő: **keresd meg, MI mondja meg helyesen** (másik
erőforrás, másik tábla), és írd le a helyesbítést. A képet
megkérdőjelezni tilos.

### Ha egy KORÁBBI kör tévedett, mondd ki

A javítás a munka része, nem kudarc. Írd le **mindkét helyen** (spec + jegy),
hogy melyik állítás dőlt meg és **mi döntötte el**. Egy téves „megfejtés"
drágább, mint egy nyitott kérdés — és a saját korábbi helyesbítésed is
lehet téves.

## 5. Munka közben

- **Nyelv**: minden chat-válasz magyarul. A felhasználó nem programozó —
  a megfejtést emberi nyelven is foglald össze, ne csak címekkel.
- **Kérdezés**: fejlesztői eldöntendő kérdést ne tegyél fel.
  **UI-döntésnél ELŐBB nézd meg a `docs/decisions/`-t** — és csak akkor
  kérdezz, ha a kérdés ott (és a jegy kommentjeiben) tényleg nincs eldöntve.

  > ⛔ **Két UI-kérdés VÉGLEGESEN eldőlt** (`docs/decisions/szerkeszto-bal-panel.md`),
  > ezeket **tilos újra feltenni**:
  > 1. **a felület PONTOSAN úgy nézzen ki, mint az eredeti Picasa** — ez az
  >    alapértelmezés minden elrendezési, méret-, térköz- és
  >    viselkedéskérdésre; ahol a kutatás megadja az eredeti mért
  >    geometriáját, azt kell követni, kérdezés nélkül;
  > 2. **a szerkesztő fülsávjában HÉT fül marad** (az eredeti öt helyett).
  >
  > A felhasználó ezt 2026-08-15-én nyomatékkal kikérte magának, miután
  > ugyanazt a két kérdést egy körön belül másodszor kapta meg.

  Ha tényleg új UI-döntés kell: **egy kérdés, javaslattal**, és a választ
  azonnal rögzítsd a `docs/decisions/`-be, hogy többé ne kerüljön elő.
- **Költség**: a Codespace-es Ghidra-kör drága és lassú (a ~10 MB-os PE32
  teljes autoanalízise 442–444 mp). Egy körben egy binárist elemezz, és
  előtte győződj meg róla, hogy az index tényleg nem elég.
