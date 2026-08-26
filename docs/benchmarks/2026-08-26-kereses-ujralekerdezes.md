# A keresési lekérdezés újrafuttatásának költsége (#1515)

*Mennyibe kerül a keresési nézet újralekérdezése egy valósághű méretű
indexen — és mennyibe az, ha csak EGY kép tagságát kérdezzük meg?*

## 1. Miért mértük

A #1515 jegy szerint a keresési nézetből nem tűnik el a kép, aminek
töröltük a feliratát. A kézenfekvő javítás a #1443 (csillagozott nézet)
mintája: a felirat mentése után futtassuk újra a nézet lekérdezését. A
keresés viszont lényegesen drágább lehet, mint a `starred_photos()`, ezért
a döntés előtt mértünk.

## 2. Módszer

- Gép: Raspberry Pi 5, Python 3.12, SQLite (a projekt saját sémája).
- Index: **140 755 kép / 3 000 mappa** — a felhasználó valódi gyűjteményének
  mérete (`docs/benchmarks/2026-08-26-dedup-gyorskulcs.md`, 4. szakasz).
  Szintetikus, de a séma és az FTS5-tartalom valódi: minden harmadik képnek
  felirata, minden ötödiknek két kulcsszava van, a mappanevek 12 szóból
  képződnek (`ANALYZE` lefuttatva, meleg cache).
- Mérés: `picasapy.index.queries.search_photos` 7 futásának mediánja
  lekérdezésenként, a rekordépítéssel együtt (ez az, amit a felület kap).

## 3. Eredmények

| lekérdezés | találat | medián | min | max |
|---|---:|---:|---:|---:|
| `search_photos("nyaralas")` | 27 179 | **597,0 ms** | 542,5 | 635,8 |
| `search_photos("IMG_000001")` | 1 | 6,2 ms | 6,0 | 6,6 |
| `search_photos("zzzkulcs")` | 0 | 6,0 ms | 5,8 | 6,2 |
| `starred_photos()` — a #1443 újralekérdezése | 7 038 | 162,1 ms | 130,4 | 243,0 |
| `all_photos()` — felső korlát | 140 755 | 3 570,4 ms | 2 800,9 | 3 856,6 |
| **egy képre szűkítve** (`only_id=…`, `"nyaralas"`), találat | 1 | **11,2 ms** | 10,7 | 12,4 |
| **egy képre szűkítve** (`only_id=…`, `"nyaralas"`), nem találat | 0 | 10,6 ms | 10,5 | 10,8 |
| **egy képre szűkítve** (`only_id=…`, `"zzzkulcs"`) | 0 | 5,8 ms | 5,7 | 6,4 |

A szűkített sorok a VÉGLEGES kóddal (`only_id=` paraméter) mértek; a felső
blokk a javítás előtti állapot. Ebből ~6 ms a 3 000 mappanév Python-oldali
`casefold`-os végigolvasása — ez a szöveges keresés fix költsége,
találatszámtól függetlenül; a maradék ~5 ms a 27 ezer soros FTS-halmaz
metszése.

## 4. Mit mond ez

1. **A keresés költségét a TALÁLATSZÁM viszi, nem az SQL.** 0 és 1 találatnál
   a lekérdezés 6 ms; 27 ezernél 597 ms. A különbség a `PhotoRecord`-ok
   felépítése.
2. **A #1443 mintája itt nem másolható.** A csillagozott nézet
   újralekérdezése 162 ms, a keresésé egy gyakori kulcsszónál ennek
   háromszorosa-négyszerese — feliratmentésenként kifizetve ez fél
   másodperces akadás a felhasználó saját gyűjteményén.
3. **Az egy képre szűkített tagság-kérdés ~50-szer olcsóbb** a drága esetben
   (11,2 ms vs 535–597 ms), és a legrosszabb esetben is a felirat mentését
   kísérő lemezírás (NAS: backup + temp + fsync) alatt marad.

## 5. A meghozott döntés

A `setCaption` utómunkája (`app/photo_ops_controller.py`,
`_refresh_if_dropped_from_search`) először **egy képre szűkítve** kérdezi meg
ugyanazt a `search_photos`-t (`only_id=` paraméter), és csak akkor futtatja
újra a teljes nézetet, ha a kép TÉNYLEG kiesett a találatok közül. A
szerkesztett kép a művelet pillanatában látszik a rácson, tehát biztosan
találat volt — így elég a kiesést vizsgálni.

Küszöb és szabad paraméter nincs a döntésben: a két ág között nem egy
becsült határérték választ, hanem az, hogy változott-e a tagság.

A tagság-kérdés SZÁNDÉKOSAN ugyanannak a függvénynek a paramétere, nem külön
„egyezik-e ez a kép" segéd — két implementáció némán elcsúszhatna
(mappanév-ág, színtokenek, idézőjel-védés), és a nézet ilyenkor hibás
tagságot mutatna. Az `index/queries.py` WHERE-jében emiatt lett zárójel az
„FTS-egyezés VAGY mappanév-egyezés" köré; enélkül a szűkítés az OR lazább
kötése miatt kibújna az FTS-ág alól. Ezt a
`tests/index/test_queries.py::TestOnlyId::test_mappanev_agat_is_szukiti`
őrzi (mutációval ellenőrizve: zárójel nélkül bukik).
