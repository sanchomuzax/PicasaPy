# #5398 2. kör: kombinált effektláncok

Ez a kör az első kör (#5295, `docs/benchmarks/2026-10-18-5295-kombinalt/`) gyanús csoportjait futtatja le. Tíz kép (a `k01.jpg`-től a `k10.jpg`-ig) ugyanabból a `minta-kombinalt` készletből készült, mint az elsőben. A `picasa.ini` a láncokat tartalmazza. A `colab-feladat.json` az első kör feladatának másolata az új ini-vel és a `#5398 2. kör` céllal.

Az ini-ben a paraméterek alakja az első kör mintáját követi: hat tizedesjegy, nyolc hexa számjegyű szín. A tagnevek a Picasa azonosítói (például `HDR`, `HeatMap`, `IR`, `Vignette`), mert a névkeresés bájtra egyezik (`docs/specs/filters-decoded.md`, #643). A `registry_data.py` kulcsai kisbetűsek, ezért az ellenőrzés kis-nagybetű nélkül futott.

## Mi maradt ki, és miért

Az 1. csoport tíz tagjából a specből csak négy dönthető el: `glow`, `HDR`, `HeatMap`, `IR`. A többi kimaradt:

- `redeye`, `retouch`: a foltok koordinátái nincsenek az ini-ben, csak a csupasz jelölő (`docs/specs/picasa-ini-format.md`, #371). A tag tényleges bemenete így nem rekonstruálható.
- `picnik`: a jelentése nincs igazolva, az élő ini-ben validálatlan jelölő (`picasa-ini-format.md`).
- `rot`: a paraméterszáma nem vezethető le a regiszterből, a spec tiltja a találgatást (`picasa-ini-format.md`, paraméterszám-korlát).
- `crop` (régi, öt számos alak): ez nem láncelem, hanem régi ini-kulcs, amit a beolvasás `crop64`-re alakít (`src/picasapy/ini/legacy_crop.py`). Láncban nincs ennek a formája.
- `ReanimatedEyeColor` (Ghoul Eye): festhető maszk. A festett vonások mezőinek egy része nincs lezárva, befestett ini-minta nincs, festés nélkül pedig nincs hatása (`docs/specs/filterdesc-registry.md`, 6. szakasz, #688).

A 2. csoportból a `focalpixelate` maradt ki: a 3.9-es natív regiszterben nincs hozzá callback (legacy, #567), ezért az eltérés effektről nem árulkodna. A `Vignette` nem került crop64 + tilt után, mert az első kör k01 ezt már futtatta. A 4. csoportban szerepel, geometriai előtag nélkül.

Mivel az 1. csoportból csak négy tag maradt, a három képen ugyanaz a négy tag van, más alapláncon és más sorrendben. Így minden kép eléri a képenkénti 3-4 tagot.

## Képenként

Minden lánc a `filters=` sorrendjében szerepel. A `Gyanú` sor azt írja le, miért gyanús az adott tag.

**k01**
- Csoport: 1. (le nem fedett tagok)
- Lánc: `autolight`, `warm`, `sat`, `glow`, `HDR`, `HeatMap`, `IR`
- Gyanú: a `glow` a régi (v1) név. A spec szerint ugyanazt a kezelőt kapja, mint a `glow2`, de élő fájlban valószínűleg csak a `glow2` fordul elő, ezt még nem igazolták. A `HDR` a natív `LocalContrast` műveletet használja, és az eredetiben a láncot az eredeti képből indítja, nem az elmosottból (#3520). A `HeatMap` LUT-ját a #3814 javította kerekítési eltérés miatt, és csak a Hue 0 és a Hue -180 esetet mérték. Az `IR`-nek az XML-ben nincs külön sora, a műveletet a natív lánc (szürkítő mátrix és elmosás) adja.

**k02**
- Csoport: 1., más alapláncon (`warm`, `sat`), fordított sorrendben
- Lánc: `warm`, `sat`, `IR`, `HeatMap`, `HDR`, `glow`
- Gyanú: ugyanazok a gyanús tagok, mint k01-ben. Az eltérő alap és a fordított sorrend azt méri, függ-e a hatás a láncban elfoglalt helytől.

**k03**
- Csoport: 1., harmadik alapláncon (`autolight`, `sat`)
- Lánc: `autolight`, `sat`, `HDR`, `IR`, `glow`, `HeatMap`
- Gyanú: ugyanazok a gyanús tagok, mint k01-ben. Itt a `HeatMap` áll a lánc végén.

**k04**
- Csoport: 2., `crop64` előtag
- Lánc: `crop64` (`08000800f800f800`), `radblur`, `Holga`, `Matte`
- Gyanú: a `radblur` kurzorpontja (x, y = 0,5) a vágott képen számol, a `Matte` keretszerű effekt, amely a vágott kép szélére kerül. A `Holga` és a `Matte` helyzetfüggő hatás, ezért a vágás után más eredményt adhatnak. Ez a #5300 osztálya.

**k05**
- Csoport: 2., `tilt` előtag (0,18)
- Lánc: `tilt`, `FocalZoom`, `radtint`, `Lomo`
- Gyanú: a `tilt` után a kép forgatott, így a `FocalZoom` középpontja és a `radtint` pontja a kiegyenesített képen van. A `Lomo` a széleken hat. Ez a #5300 osztályába tartozik: geometria a helyzetfüggő effektek előtt.

**k06**
- Csoport: 2., `crop64` előtag
- Lánc: `crop64` (`08000800f800f800`), `Polaroid`, `RoundedEdges`, `radsat`
- Gyanú: a `Polaroid` keretet ad, és a keret arányát a kép rövidebb oldala adja. A `RoundedEdges` sarkai és a `radsat` pontja így már a keretezett képen számol. Az első körben a Polaroid egy másik erős réteg után tért el (k03), itt más az előzmény.

**k07**
- Csoport: 3., erős előző réteg, utána keretek
- Lánc: `dir_sat`, `blur`, `Matte`, `RoundedEdges`
- Gyanú: az első körben a `dir_sat` és a `blur` után álló `Polaroid` tért el (k03, #5299). Itt ugyanaz az erős réteg, de Polaroid nélkül. Így kiderül, a hiba a Polaroidhoz kötődik-e, vagy a keretekhez általában.

**k08**
- Csoport: 3., erős előző réteg, utána Polaroid és keret
- Lánc: `PencilSketch`, `Polaroid`, `MuseumMatte`
- Gyanú: a `Polaroid` más erős réteg (`PencilSketch`) után áll, mint az első körben. A `MuseumMatte` két színnel, külső és belső kerettel dolgozik.

**k09**
- Csoport: 4., A sorrend
- Lánc: `sat`, `Vignette`, `dir_tint`, `Matte`, `colortemp`, `radblur`
- Gyanú: a hat tag színes (`sat`, `dir_tint`, `colortemp`) és geometriai (`Vignette`, `Matte`, `radblur`). A `Vignette` az első körben vágás és kiegyenesítés után tért el (#5300). Itt nincs geometriai előtag, így a sorrend a vizsgált változó.

**k10**
- Csoport: 4., B sorrend (a k09 fordítottja)
- Lánc: `radblur`, `colortemp`, `Matte`, `dir_tint`, `Vignette`, `sat`
- Gyanú: ugyanaz a hat tag, fordított sorrendben. Ha a k09 és a k10 eredménye eltér, akkor a sorrend a gyanús, és a felezés a következő lépés.

## Ellenőrzés

- A `colab-feladat.json` érvényes JSON (`python3 -m json.tool`).
- Minden tag megvan a `src/picasapy/render/registry_data.py` kulcsai között.
- A paraméterszámokat kézzel ellenőriztem a regiszter csúszkáival és a `filterdesc-registry.md` 4.1/b szakaszának sorrendjével. A puckos tagoknál (`radblur`, `radsat`, `radtint`, `dir_tint`, `FocalZoom`) a két koordináta is benne van.
- Kódhoz nem nyúltam, a CI-őrök nem futottak.

## Nincs benne

- A Colab-feladat nincs futtatva. A ΔE-értékek a futás után jönnek.
- A `docs/specs/paritas-ellenorzes.md` nem változott.
