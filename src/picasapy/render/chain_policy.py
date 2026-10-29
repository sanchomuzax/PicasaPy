"""A `filters=` lánc ismert nevei, kihagyási okai és üzenetei."""

from __future__ import annotations

#: Az exe-string-bányászat (`docs/specs/picasa-exe-strings.md`, #347) által
#: AZONOSÍTOTT, de golden-méréssel MÉG NEM KALIBRÁLT `filters=` nevek. A lánc
#: FELISMERI őket — parse/round-trip rendben megy, és az `apply_filters`
#: kihagyott-listájában (`skipped`) szerepelnek, tehát az összesített
#: "nem renderelhető" jelentésbe számítanak —, de VIZUÁLIS MODELLT nem
#: futtatunk rájuk: kitalált implementáció helyett a kalibráció a #347
#: utódjegyében (golden-kör) készül el. A `RECOGNIZED_BUT_UNRENDERED`
#: elnevezés szándékos: megkülönbözteti őket a TELJESEN ismeretlen
#: (soha nem dokumentált) nevektől, amik ugyanabba a `skipped` listába
#: kerülnek, de nincs mögöttük exe-forrás.
KNOWN_UNRENDERED_OPS = frozenset(
    {
        # `grain` (v1) a #347 lezáró auditban (2026-08-06) KIKERÜLT innen:
        # a `filterdesc-registry.md` szerint a `grain2`-vel MEGEGYEZŐ,
        # paraméter nélküli "Film Grain" oneclick család régi tagja. A
        # #3927/#3928 a natív munkafüggvényt (0x0090a2e0) a bináriból
        # olvasta ki: a callback mindkettőt azonos `a = 0,5`-tel hívja,
        # tehát nem "más algoritmus, kölcsönzött modellel", hanem EGYETLEN
        # algoritmus — ezért fut mindkettő az `_apply_grain_op`-on (ld.
        # lent a `_HANDLERS`-ben).
        # `radtint` a #565-ben KIKERÜLT innen: a natív regisztráció
        # (0x8f8730), a feldolgozó mag (0x90b370) és a maszk-LUT (0x90aeb0)
        # visszafejtésével az algoritmuscsalád és a pixelművelet (radiális
        # szorzó-tint, köbös smoothstep maszk) rögzített; a közös natív
        # sugaras súlytáblát használja (ld. apply_radtint).
        # --- a filterdesc-regiszter (#382) által azonosított 21 további,
        # eddig sehol nem dokumentált szűrőnév — a filterdesc.xml-ben
        # léteznek, tehát régi könyvtárak `filters=` láncában előfordulhatnak.
        # A regiszterben (`registry.py`) megvan a leírásuk, de vizuális
        # modellt (golden-mérés híján) még nem futtatunk rájuk.
        # `triple`, `triple2`, `triple3`, `autocontrast`, `colortemp`,
        # `contrast`, `gamma`, `backlight`, `shadow` a #687-ben KIKERÜLT innen: a
        # dekompilált burkolóikból (`natív-szűrők.c`) a csúszka →
        # munkafüggvény-argumentum leképezés egyértelmű, a munkafüggvények
        # pedig már megvoltak. A #685 mérőszettje mindegyiket igazolta
        # (ld. a `chain_native_handlers` docstringjeit) — a `triple`
        # kivételével, aminek az egyetlen mérőesete paraméter nélküli
        # (tehát azonosság) volt.
        "colorfix",
        # #5304: a `rainbow` kikerült a kalibrálatlanok közül; a teljes
        # algoritmus a `render/rainbow.py`-ban, a #5296 spec szerint fut.
        # `linblur` és `dir_sharp` a #623-ban KIKERÜLT innen: a natív magok
        # (`0x0090de10`, `0x0090d600`), a burkolóik és a közös elmosó
        # (`0x009dd0d0`) visszafejtésével a hatás jellege és a
        # pixel-matematika rögzített. A `linblur` sugár-leképezése és a
        # `dir_sharp` rámpa-horgonya KÖZELÍTÉS — ld. a két `apply_*`
        # docstringjét; a kalibráció a #317-ben fut.
        # A `blur` a #1142-ben KIKERÜLT innen: a `merokit-2` szett három
        # csúszkaállása kimérte, hogy a csúszkatartományon KÍVÜLI küszöbnél
        # valódi, σ = 4,0 szórású elmosást ad (ld. `render/blur.py`).
        "whitept",
        "debug",
    }
)

#: #567 — HALOTT (legacy) szűrőnevek: a `filterdesc.xml`-ben még ott állnak,
#: de a 3.9.141.259 build natív regisztrációs táblájában NINCS hozzájuk sem
#: render-callback, sem névregisztráció. Ezek tehát nem „még nem
#: implementált" effektek: maga a Picasa sem futtatta már őket, konfigurációs
#: maradványok. A lánc kihagyja őket (a `skipped`-ben megjelennek), és a
#: `ChainReport.legacy_warnings` külön, egyértelműen kimondja, hogy halott
#: bejegyzésről van szó.
#:
#: A kisbetűs `focalpixelate` NEM azonos az élő `PicnikFocalPixelate`
#: Glimmer-effekttel: az utóbbi saját néven, saját callbackkel regisztrált,
#: és a saját handlerén fut. A kettőt szándékosan nem vezetjük egy kulcsra.
DEAD_LEGACY_OPS = frozenset({"focalpixelate"})

#: #687 — MÉRTEN TÉTLEN szűrőnevek: a #685 mérőszettjében (178 kép, egyetlen
#: valódi Picasa-export) maga a Picasa sem változtatott rajtuk (átlagos
#: ΔE ≤ 1,0, ami a JPEG-újratömörítés szintje), holott a lánc a
#: `filterdesc.xml` szerinti alap-, felső és alsó csúszkaállásokat is
#: tartalmazta.
#:
#: **Ez NEM azonos a `DEAD_LEGACY_OPS`-szal.** Ezeknek a natív regiszterben
#: VAN feldolgozójuk (a `colorfix`/`whitept` a `0x0090eda0` fehérpont-magot
#: hívja) — csak a mérésben nem hatottak.
#: Két magyarázat áll nyitva, és a mérés egyik mellett sem dönt:
#: vagy tényleg tétlenek a 3.9.141.259-ben, vagy a mérőszett által
#: generált paraméter-alak nem az, amit a Picasa olvas (a `colorfix` és a
#: `whitept` PIPETTA-színt vár, amit a szett a lánc végére írt). Ezért a
#: bejegyzés célja pusztán annyi, hogy a következő mérés ne HIÁNYNAK
#: olvassa őket: a felhasználó a lánc kihagyásakor megkapja az okot is.
#:
#: ⚠️ A `blur` a #1142-ben KIKERÜLT innen. A #685-ös mérés csak a
#: `filterdesc.xml` csúszkatartományát (`[-0,5; 0,5]`) járta be, és ott
#: tényleg tétlen — a `merokit-2` szett viszont a tartományon KÍVÜLI
#: `blur=1,2.000000;` alakot is kimérte, és az VALÓDI elmosást ad. A
#: „mérten tétlen" tehát a MÉRT tartományra szólt, nem a szűrőre.
MEASURED_IDLE_OPS = frozenset({"colorfix", "whitept"})

#: #1142 — MÉRTEN NEM FUTÓ szűrőnevek: a `merokit-2` szettben az eredeti
#: Picasa a FORRÁST adta vissza rájuk, miközben nálunk volt hozzájuk
#: renderer, tehát a mi kimenetünk némán ELTÉRT az eredetiétől.
#:
#: ⚠️ A `picnikfocalpixelate` 2026-09-22-én KIKERÜLT innen (#3315). A
#: binárisból kiolvasva a lánc-ÍRÓ (`0x0042abcc` `"%s=%s;"`, a név a
#: leíró `+0x14` mezőjéből, `0x008f6bc0`) és az értékrész mezősorrendje
#: (`0x008fac40`: engedélyezés → puck x,y → 3 csúszka → szín(ek) → a
#: NEGYEDIK csúszka → jelölőnégyzetek `,%d`) szerint a helyes alak
#: **nyolcmezős**:
#:     `PicnikFocalPixelate=1,x,y,Impact,Radius,Hardness,Fade,Reverse;`
#: A #1142 mérése hét- és négymezős sorral készült, tehát ROSSZ ARITÁSÚ
#: bemenetet mért — ugyanaz a hibaosztály, mint a #2948 kisbetűs láncai.
#: A betöltő úton semmi nem zárja ki a szűrőt: a név a `filterdesc.xml`
#: regiszterében van, a gyártó (`0x008f9fe0`) a közös Glimmer-feldolgozót
#: (`0x008f9a60`) építi rá, és a beolvasó ugyanazokkal a jelzőkkel tölti
#: fel a mezőket, amikkel az író kiírta. Pozitív kontroll: a `FocalZoom`
#: ugyanilyen leíró jelölőnégyzet NÉLKÜL — ott a hétmezős alak a TELJES
#: alak, és mérten LEFUT.
#: A nyolcmezős alak golden-mérése külön jegy; addig rendereljük, mert a
#: bizonyíték a futás mellett szól, a tétlenség mellett pedig csak egy
#: érvénytelen aritású mérés szólt.
MEASURED_NOT_RUNNING_OPS: frozenset[str] = frozenset()

#: A mérten tétlen bejegyzésre adott, felhasználónak szóló magyar üzenet.
MEASURED_IDLE_WARNING_TEMPLATE = (
    "{name}: a mérésben (#685) maga a Picasa sem változtatott vele a képen, "
    "ezért nem futtatunk rá modellt — a kép változatlan marad."
)

#: A mérten NEM FUTÓ bejegyzésre adott, felhasználónak szóló üzenet (#1142).
MEASURED_NOT_RUNNING_WARNING_TEMPLATE = (
    "{name}: a mérésben (#1142) maga a Picasa sem futtatja le ezt a "
    "szűrőt, ezért mi sem futtatjuk — a kép változatlan marad."
)

#: #910 — a FÖLÖS paraméterű tagra adott, felhasználónak szóló üzenet.
#: Az eredeti Picasa lánc-bejárója az ilyen tagot elejti (a `filterdesc.xml`
#: csúszkaszáma a felső korlát); mi eddig csak az ÍRÁS útvonalán
#: érvényesítettük a `MAX_PARAM_COUNTS` táblát, a renderelésen nem.
EXCESS_PARAM_WARNING_TEMPLATE = (
    "{name}: több paramétere van ({count}), mint amennyit a szűrő ismer "
    "({limit}) — a Picasa az ilyen bejegyzést elejti, ezért a kép "
    "változatlan marad."
)

#: A halott bejegyzésre adott, felhasználónak szóló magyar üzenet (#567).
#: #567: az `autobacklight` fix derítőfény-erőssége a natív hívás
#: argumentumából (0,25) — nem csúszka, nem képfüggő.
_AUTOBACKLIGHT_FILL = 0.25

DEAD_LEGACY_WARNING_TEMPLATE = (
    "{name}: halott (legacy) szűrőnév — a Picasa 3.9 natív regiszterében "
    "sincs hozzá feldolgozó, ezért a kép változatlan marad."
)

#: Boolean jelző-tokenek a láncban (`<név>=1;`, param nélkül), amik NEM
#: effektet írnak le, hanem egy másik bejegyzés melletti METAADATOT — mint a
#: már ismert `redeye=1;`/`retouch=1;`. A `picnik=1;` (exe-string-bányászat,
#: #347) feltehetően azt jelzi, hogy a lánc valamelyik tagja Creative
#: Kit ("Picnik") eredetű effekt volt. Ezeket a lánc ÉRVÉNYES no-op-ként
#: nyeli el: nem effekt, ezért nem is kerül a "nem renderelhető" kihagyott-
#: listába — az ini-round-trip a `picasapy.ini.filters` generikus
#: parse/serialize rétegén keresztül változatlanul megőrzi.
#: A #382-es filterdesc-regiszter öt `mode="history"`/mozi-jelölő szűrője:
#: nem képi művelet (csak szerkesztési előzmény vagy mozi-vágás-marker),
#: ezért ugyanúgy no-op-ként nyelendők el, mint a `picnik=1;`.
_NOOP_MARKERS = frozenset({"picnik", "save", "rot", "crop", "moviestart", "movieend"})
