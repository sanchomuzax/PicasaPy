# A restaurátor szerszámosládája — módszertan zárt bináris feltárásához

Ez a lap **eszközkatalógus**, nem eredménygyűjtemény. Azért készült, hogy egy
későbbi kör ne kezdje elölről a gondolkodást: minden szerszám mellett ott áll,
**mit hozott ki itt**, **mikor kell érte nyúlni**, és **mit NEM lát**.

A vezérelv: az őskövület nem egyben adja ki magát. Minden szerszám más réteget
bont — és a legtöbb lelet **két szerszám metszéspontjában** van.

Forrás, amin mindez kipróbálva: Picasa 3.9.141.259 telepítése
(`research/copy_Picasa_3_7/Picasa3/`).

---

## 1. Szövegkinyerés — mindkét kódolásban

```sh
strings -n 5    Picasa3.exe  >  all.txt
strings -n 4 -el Picasa3.exe >> all.txt      # UTF-16LE — enélkül a fele elvész
```

**Mit hozott:** a `.picasa.ini` teljes kulcs-szótára, a virtuális albumok
`]`-prefixes listája, a parancssori kapcsolók, a registry-kulcsok.

**Amit NEM lát:** az **ékezetes UTF-8** szöveget. A `strings` minden 2 bájtos
UTF-8 karakternél megszakad — a `Picasa3i18n.dll` magyar szövegét így
**lehetetlen** kinyerni. Arra a 4. szerszám kell.

---

## 2. A szomszédság a jelentés ⭐ *(a legtermékenyebb szerszám)*

A fordító a string-táblába **forráskód-közelségben** rakja a szövegeket. Egy
találat önmagában semmit nem ér; a **környezete** kiadja az egész funkciót.

```sh
n=$(grep -n "keresett" all.txt | head -1 | cut -d: -f1)
sed -n "$((n-25)),$((n+25))p" all.txt | tr '\n' '|'
```

**Mit hozott — mindegyik EGY blokkból, nem külön keresésekből:**

| lelet | a blokk |
|---|---|
| a `.picasa.ini` 38 kulcsa | egyetlen tömb `parent`-től `backuphash`-ig |
| a kollázs 9 téma-kulcsa | `polaroid…framegrid` egy sorban |
| a 18 film-átmenet | név + belső kulcs párokban |
| a hisztogram kamera-formátumai | `il_NerdView::1..7` egymás után |
| a 10 `color:` keresőtoken | `avgcolor` közvetlenül mellettük |

**Szabály:** ha egy keresés egy találatot ad, **nem végeztél** — nézd meg a
környezetét. Ha nulla találatot ad, keress rokon szót és nézd ANNAK a környékét.

---

## 3. RTTI-osztálynevek — amikor a szöveg hallgat

MSVC-vel fordított binárisban a C++ típusinformáció **bennmarad**:

```sh
grep -oE "\.\?AV[A-Za-z_0-9]*Kulcsszo[A-Za-z_0-9@]*" all.txt | sort -u
```

**Mit hozott:**
- `CNevenVisionDLL::IFace`, `vbf_Cascade`, `epi_PoseEst` → **az arcfelismerő motor
  azonosítása** (Neven Vision) — erről egyetlen felhasználói szöveg sem szól.
- `HOGSimilarityComputer` → a **hasonlósági keresés** algoritmusa.
- `LayoutPassport`, `LayoutRegularGrid` → a **nyomtatási elrendezés-motor**.
- `CPileTheme`, `CFrameGridTheme`, `CMultiExposureTheme` → a **kollázs-témák**
  megerősítése.
- `CRetouchFilter`, `PatchEdit` → a retusálás **foltonkénti** adatmodellje.

**Mikor nyúlj érte:** ha egy funkcióról tudod, hogy létezik, de a UI-szövegek
nem árulják el a *mechanizmust*. Az osztálynév gyakran megmondja az algoritmus
családját.

---

## 4. Beágyazott, jól formált XML — ne regexeld a binárist

A `Picasa3i18n.dll` **teljes XML-dokumentumokat** tartalmaz. Ne szövegdarabokra
vadássz, hanem **a dokumentumhatárokat** keresd, és a kivágott blokkot már
rendes parserrel dolgozd fel.

```python
pat = b'<?xml version="1.0" encoding="utf-8" ?>\n<resources>'
i = 0
while (i := d.find(pat, i)) >= 0:
    j = d.find(b'</resources>', i)
    blokk = d[i:j+12].decode('utf8')      # ettől már ép XML
    i = j + 12
```

**Mit hozott:** 1642 blokk, **4031 egyedi azonosító, 41 nyelven**, benne a
**418 menüparancs** hivatalos magyar felirattal. Egy korábbi kör ezt
ékezet-heurisztikával próbálta, veszteséggel; így **hiánytalan**.

**Nyelv-azonosítás:** ha nincs nyelvcímke, keress egy **önleíró** stringet — itt
az `options/item27.title` minden nyelvi blokkban a „System Default (xx-XX)"
szöveget tartalmazza, ami kiadja a nyelvet.

---

## 5. Formátum-sztringek = specifikáció

Minden `%`-ot tartalmazó string egy **szerializációs formátum**. Keresd őket a
funkció neve közelében.

**Mit hozott:**
- `conf(%.3f),pan(%.3f),leye(%.3f,%.3f),reye(…),mouth(…)` → az **arc-részletadat**
  teljes formátuma
- `crop=rect64(%s)`, `rotate(%d)`, `flipped(%d)`, `%s=%s;` → az ini-szintaxis
- `1/%ds` és `%2.1fs` → a záridő **két** alakja a hisztogram-panelen
- `Moving %d of %d (%s/s)` → a haladásjelzés sebességgel

**Fordítva is igaz:** ha egy mezőhöz **nincs** formátum-sztring (`text=`, `redo=`,
`retouch` régió), az erős jel, hogy **nem szövegesen** szerializálódik, vagy
kódba égetett — ott a bináris-kutatás zsákutca, mérés kell.

---

## 6. Ismeretlen konténer feltörése — négy lépés

Ne fogadd el, hogy „dokumentálatlan bináris". A `respack.yt`-ról két kör is azt
mondta, hogy megfejthetetlen; négy lépésben megtört:

1. **A fájl eleje**: az első `uint32` gyakran **offset vagy darabszám**.
   Itt: a névindex helye a fájl végén.
2. **A fájl vége**: keress **olvasható neveket** — az index majdnem mindig
   szöveges. Innen derül ki a bejegyzések száma és névtere.
3. **Fejléc-hipotézis a legegyszerűbb bejegyzésből**: keress olyat, aminek a
   *jelentését* sejted. Itt a `docbounds` nevű elem → a benne lévő két szám
   nyilván **szélesség/magasság** → ebből kiderült a 4×`int16` határoló doboz.
4. **⭐ Ellenőrzés invariánssal**: találj ki egy szabályt, aminek *teljesülnie
   kell*, és futtasd az ÖSSZES bejegyzésre. Itt: a kifejtett képpontszámnak
   pontosan `(x1−x0)·(y1−y0)`-nak kell lennie. **2769/2769 stimmelt** — ettől
   lett hipotézisből bizonyosság.

**Ez a 4. lépés a legfontosabb.** Enélkül csak „valószínűleg jó" van; vele
tudod, hogy kész.

**Csapda, amit itt fogott:** a koordináták **előjelesek** (`int16`). Előjel
nélkül 17 réteg mérete értelmetlenné vált — az invariáns ezt azonnal kimutatta.

---

## 7. A konténerben szöveg is lehet

Miután feltörted a csomagot, **nézd meg, mely bejegyzések nyomtathatók**.

**Mit hozott:** a `respack.yt` 2909 bejegyzéséből **140 tiszta ASCII** — a Picasa
**teljes UI-elrendezés-forráskódja** (`.tre`), makrókkal, kényszerekkel,
eseménykezelőkkel és **kikommentezett fejlesztői jegyzetekkel**.

Innen jött: a panel-navigáció (`showtarget`/`hidetarget`), a mappa-fejléc
tipográfiája, a szerkesztő fül-szerkezete, és annak bizonyítéka, hogy a
Canon-panel **soha nem került be** (minden vezérlője rejtett).

---

## 8. Az alkalmazás SAJÁT definíciós fájljai — ide nézz ELŐSZÖR

A `runtime/` mappában ott volt a `filterdesc.xml`: a Picasa **saját, gépi
olvasásra szánt** szűrő-regisztere. 84 szűrő, csúszkánként név/tartomány/
alapérték, és a 33 kreatív effekt **teljes csővezetéke** görbékkel.

**Ez hónapnyi golden-mérést váltott ki** — és két körön át észrevétlen maradt,
mert senki nem nézte meg a `runtime/` mappa XML-jeit.

**Szabály:** mielőtt viselkedést mérnél vagy algoritmust fejtenél vissza, **fésüld
át az alkalmazás konfigurációs és definíciós fájljait** (`*.xml`, `*.ini`,
`*.txt`, `*.fen`, `*.ui`). Amit az app magának deklarál, azt nem kell kitalálni.

---

## 9. PE-erőforrás-fa — a szabványos réteg

```python
# opcionális fejléc → DataDirectory[2] = RESOURCE → RVA→fájlpozíció → könyvtárfa
```

**Mit hozott itt:** 13 **natív Win32 dialógus** és 19 **string-tábla blokk**
(265 string) — plusz a **negatív** bizonyíték: **nincs `RT_MENU` és nincs
`RT_ACCELERATOR`**. Ez zárta le véglegesen a billentyűparancs-kérdést: a menük
és a gyorsbillentyűk **kódban épülnek**, nem erőforrásból.

**Mikor nyúlj érte:** ha menü-, dialógus- vagy gyorsbillentyű-szerkezetet
keresel. **Windows-programnál ez az első hely** — nálunk azért lett a kilencedik,
mert a Picasa saját UI-motort használt.

---

## 10. Kereszt-hivatkozás: ahol két névtér egybeesik

A legnagyobb ugrás akkor jött, amikor kiderült, hogy **négy különböző forrás
ugyanazt a névteret használja**:

```
respack.yt  layer:<panel>/<elem>     →  a grafika
respack.yt  tre:<panel>              →  az elrendezés és a viselkedés
respack.yt  tre:<panel>_text         →  a felirat KÖTÉSE
i18n.dll    <stringres id="<panel>/<elem>.title">  →  a felirat 41 nyelven
```

Ettől lett a négy külön adathalmazból **egyetlen, gépileg összekapcsolható
modell**.

**Szabály:** ha két forrásban ugyanolyan alakú azonosítót látsz, **ellenőrizd,
hogy ugyanaz-e**. Ha igen, minden összejoinolható — és onnantól a kérdés nem
„hol van?", hanem „melyik táblából olvassam ki?".

---

## 11. Valódi felhasználói adat mint kontrollminta

A mért/kinyert értékeket **valódi adaton** kell hitelesíteni.

**Mit hozott:** a `Vignette=1,35.000000,1.400000,0.000000,00000000` valós
`.picasa.ini`-sor **bájtra egyezett** a `filterdesc.xml` alapértékeivel — ettől
lett a regiszter bizonyított igazságforrás, nem csak dokumentáció. A `.cxf`
mintafájl pedig egyetlen lépésben eldöntötte a kollázs-formátumot.

**Szabály:** ha van valódi adat, **azzal kezdd az ellenőrzést**, ne a végén.

---

## 12. Élő vs. holt kód megkülönböztetése

Egy erőforrás megléte **nem** jelenti, hogy a funkció kiszállított.

**Három próba:**
1. Szerepel-e a panel **azonosítója** a lefordított string-táblában? (A Canon-panelé
   nem — tehát soha nem lett bekötve.)
2. A rétegek `m_hidden` / `enable="0"` állapotúak-e?
3. A `.tre`-ben **ki vannak-e kommentezve** a sorok? (A fejlesztők jegyzetei
   gyakran meg is mondják: *„hidden for now and might be used in the future"*.)

**Mit hozott:** a Canon live-view panel és a „rendezés szín szerint" mód is
**megírt, de ki nem adott** funkciónak bizonyult.

---

## 13. Az explicitebb forrás nyer

Ha két forrás mást mond, **ne a frissebbet vagy a kényelmesebbet válaszd, hanem
az explicitebbet.**

- `<placement>4.0` **>** a fájlbeli deklarációs sorrend (kényszeres elrendezésnél
  a sorrend nem pozíció!)
- valódi adatfájl értéke (`picturepile`) **>** ikonnévből tippelt kulcs (`pile`)
- mért golden **>** a doksi állítása

**Két hibát fogott meg utólag** ebben a munkában — mindkettő már jegyben volt,
amikor kiderült.

---

## 14. A negatív eredmény is eredmény

Rögzítsd, ha valamit **bizonyíthatóan nem lehet** kinyerni — különben egy
későbbi kör újra nekifut.

Itt így zárult le: a gyorsbillentyű-lista (nincs `RT_ACCELERATOR`, a súgó online
volt), a `redo=` szemantikája (nincs formátum-sztring), a `text=` felépítése, a
retus-régiók kódolása. Mind a négy **méréssel** oldható meg, kutatással nem.

---

## Még fel nem emelt kövek

| kő | mit adhat | költség |
|---|---|---|
| ~~**`red.cfg` szerkezete**~~ | **LEZÁRVA (2026-08-07):** entrópia **7,2–7,4 bit/bájt** a fájl egészében → **tömörített vagy sűrűn kvantált** adat; nincs olvasható szöveg, nincs értelmes float-tömb; ismétlődő 4 bájtos rekord-jelölő (`00 03 17 00`). A modell a motor nélkül nem fejthető ki — **és nem is használható**: a Google tanított súlyai. | — |
| **Import/export tábla** (mely DLL-függvények) | képesség-térkép: mit tudott natívan | kicsi, közepes haszon |
| ~~**`.rdata` konstans-táblák**~~ | **LEZÁRVA (2026-08-07): a szűrő-görbék NINCSENEK beégetve.** Ld. lent. | — |
| **13 natív dialógus** (`RT_DIALOG`) | a korai/rendszerszintű ablakok | kicsi |
| **`.ytf` betűtípus-formátum** | előre renderelt glyphek | nincs rá szükség |
| **Diszasszemblálás** | minden, ami nem adat | aránytalanul nagy |

### A konstans-tábla-kutatás eredménye (2026-08-07) — NEGATÍV, de nem üres

Módszer: a `.rdata` és `.data` szakaszokban 256 elemű **monoton** bájtsorozatok
keresése, majd összevetés a mért görbéinkkel (`research/golden-analysis/luts*.json`),
plusz külön pásztázás 256 elemű float-tömbökre.

**Eredmény: kilenc monoton bájt-tábla, EGY float-tömb — és egyik sem szűrő-LUT.**
A mért görbéinkkel egyik sem egyezik (a legjobb „találat" az identitás-tábla volt,
ami triviálisan illeszkedik a közel-identitás mérésekre). **A Picasa a szűrőgörbéket
futásidőben számolja, nem táblából olvassa.** A #317 golden-köre tehát nem
rövidíthető le ezen az úton.

Amit viszont **sikerült azonosítani** (mindkettő ±1 pontossággal illeszkedik a
modellre):

| hely | tartalom | modell |
|---|---|---|
| `.data` @0x932bcc | **a „Mac gamma (1,6)" megjelenítési mód táblája** | `255·(x/255)^(1,6/2,2)` — mért 94/155/206, modell 93/154/207 |
| `.rdata` @0x86bc1b | 1024 elemű **négyzetgyök-tábla**, 0…180 kimenettel | `180·√(i/1023)` — mért 0/89/127/156/180, modell 0/90/127/156/180 |

Az első **bizonyíték arra, hogy a Nézet menü „Megjelenítési mód" almenüje
(#443, #427) valódi, implementált funkció volt**, nem UI-maradvány.

**Módszertani tanulság:** a negatív eredmény itt is hasznos — de csak azért volt
kimondható, mert volt **mért kontrollmintánk**, amivel össze lehetett vetni. Tábla-
kereséshez mindig legyen ground truth, különben a találatok azonosíthatatlanok.

---

## 15. Validációs LÉTRA — nem egy ellenőrzés, hanem több fok

*(Forrás: az LLM-alapú bináris-visszafejtés kutatása — AutoDecompiler, FORGE,
Kong, ReF Decompile, SentinelOne „Gauntlet". A saját munkánkra átültetve.)*

A 6. pont invariáns-ellenőrzése **egyetlen fok**. A kutatási irodalom
**fokozatos létrát** használ, ahol a bukás *helye* megmondja, milyen jellegű a
hipotézis-hiba. Konténer-formátumra átültetve:

| fok | mit ellenőriz | mit jelent a bukás |
|---|---|---|
| 1 | az index parse-olható | rossz a fejléc-elmélet |
| 2 | a rekordok **hézag és átfedés nélkül lefedik** a fájlt | rossz a rekordhatár-szabály |
| 3 | minden rekord deklarált mérete stimmel | rossz a méretmező |
| 4 | a kifejtett adat teljesíti a szemantikai invariánst | rossz a payload-értelmezés |
| **5** | **a visszakódolt bájtsor AZONOS az eredetivel** | **a részletek nem pontosak** |

**Az 5. fok a döntő, és nekünk hiányzott.** A `respack.yt`-t a 4. fokon
„100%-ban megfejtettnek" nyilvánítottuk — a round-trip próba viszont **1025
rétegen eltérést mutatott**, és kiderült, hogy az RLE-futamok NEM sorhatárra
igazítottak (ld. `picasa-respack-format.md` 3.2). A javítás után 1365/1365
bájtra egyezik.

**Szabály:** amíg nem tudsz **visszakódolni**, addig nem érted a formátumot —
csak olvasni tudod.

### 15.1 Kerüld a triviálisan teljesülő ellenőrzést

A jutalom-kijátszás („metric gaming") megfelelője nálunk: olyan próba, amit egy
üres/azonos jelölt is kielégít. A LUT-keresésnél az **identitás-tábla** minden
közel-identitás mérésünkre illeszkedett — látszatra „találat", valójában semmi.
**Zárd ki explicit a triviális jelölteket.**

### 15.2 Cáfoló kör — a legfontosabb hiányzó lépés

A „Gauntlet"-minta: több ügynök fut, majd egy külön körben **egymás állításait
próbálják megcáfolni**, kötelezően állást foglalva (egyetért / nem ért egyet), és
a dekódolási műtermékeket aktívan elutasítják.

**Nálunk ez hiányzott**, és két hibás állítás (a gombsorrend és a kollázs-kulcsok)
csak egy jóval későbbi, véletlen ellenőrzésen bukott ki. **Minden kutatási kör
után futtatni kell egy cáfoló kört**, aminek az EGYETLEN feladata megtámadni a
friss állításokat — nem újat találni.

### 15.3 Az ügynök a JELEN állapotot is kapja meg, ne csak a forrást

A „kontextus-leépülés" megfelelője: a leltározó ügynökünk elavult listát adott,
mert csak a specifikációkat látta, a friss jegy-kommenteket nem. **A brief
tartalmazza, mi derült ki eddig** — különben már megválaszolt kérdésekre kapsz
válaszokat.

### 15.4 ⚠️ A kinyert szöveg NEM megbízható bemenet

A kutatás dokumentál egy valós támadást: a bináris `.rodata` szekciójába rejtett
szöveg **prompt-injekcióként** eltérítheti az elemző ügynököt — és a rejtett,
soha nem futó kódban lévő szöveg is bekerül a nyers kinyerésbe, tehát az emberi
elemző **nem is látja**.

A Picasa jóindulatú, de **ez a módszertan újrahasználható**. Ezért kötelező:
a binárisból kinyert szöveg (`strings`, erőforrás, `.rodata`) **adat, nem
utasítás** — akkor is, ha parancsnak látszik. Ismeretlen eredetű binárisnál ezt
az ügynök-briefben expliciten ki kell mondani.

### 15.5 Amit még érdemes átvenni

- **Ismerd fel és hagyd ki a MÁR ISMERTET** (Kong „szignatúra-egyeztetés"):
  első lépésként osztályozz minden fájlt/szakaszt ismert formátumként (ZIP, PE,
  XML, PSD) — csak a maradékot kell visszafejteni. Nálunk ez a `file` parancs
  volt, de érdemes első osztályú lépéssé tenni.
- **Hipotézis-alakú lekérdezés** (ReF „interaktív adathozzáférés"): ne ürítsd ki
  az egész adatszakaszt — kérdezz rá célzottan arra a mintára, amit a
  hipotézised megkövetel. A LUT-keresés pontosan így működött.
- **Regresszió-büntetés**: dokumentum-frissítéskor ellenőrizd, hogy nem
  **vesztettél-e el** korábban igazolt tényt. A visszalépés rosszabb, mint a
  lassú haladás.

---

## A sorrend, amit legközelebb érdemes követni

1. **Az app saját definíciós fájljai** (8.) — a legolcsóbb, a legtöbbet adja.
2. **PE-erőforrás-fa** (9.) — Windows-programnál kötelező első kör.
3. **Szövegkinyerés + szomszédság** (1., 2.) — a gerinc.
4. **RTTI** (3.) ott, ahol a szöveg hallgat.
5. **Beágyazott XML** (4.) a lokalizációhoz.
6. **Konténer-feltörés** (6., 7.) — csak ha a fentiek után is marad fehér folt.
7. **Kereszt-hivatkozás** (10.) — folyamatosan, minden körben.
8. **Hitelesítés valódi adaton** (11.) és **élő/holt szűrés** (12.) — a végén,
   mielőtt bármit jegybe írnál.
