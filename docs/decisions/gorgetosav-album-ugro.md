# ADR-015: A görgetősávon MEGÉPÜL az album-ugró gombpár — a sáv stílusa marad

Dátum: 2026-09-19 · Státusz: ELFOGADVA · jegy: #857 (előzmény: #856)

> **Egymondatos összefoglaló:** az eredeti Picasa görgetősávjának négy gombja
> közül a két **album-ugrót** megépítjük (a rács sávjának tetején az előző, az
> alján a következő albumra ugrik, nyomva tartva ismételve), a sáv **rajzát és
> a fel/le nyílgombokat viszont nem** — az navigáció, ez stílus.

## A helyzet

A #856 mérése szerint az eredeti sávján **négy** gomb van: `prevalbum`,
`albumscrolltop`, `albumscrollbottom`, `nextalbum` — mind 16 × 24, mind
`m_autorepeat`, három állapotképpel, két platformra külön megrajzolva
(`respack.yt` `scrollart/` 46 és `throttle/` 22 rétege, `throttle.tre`).

Nálunk a `PicasaScrollBar` 10 képpontos, lapos sáv, gombok nélkül. A #857
kimondta, hogy ebből **az album-ugrás nem stílus, hanem NAVIGÁCIÓ**: a
felhasználó ezzel lépked a mappák/albumok között anélkül, hogy a görgetőt
végighúzná.

## A döntés

A tulajdonos 2026-09-18-án döntött:

> Legyen két külön gomb a görgetősávon is, ugyanúgy, mint az eredetiben.

Ezért:

1. **Megépül** a két album-ugró gomb — a RÁCS görgetősávján (`feedScrollBar`).
   Fent az előző, lent a következő album; **nyomva tartva ismételnek**, ahogy
   az eredeti `m_autorepeat` mezője előírja.
2. **Nem épül meg** a fel/le nyílgombpár, a lapozó féltér és a pozíciójelző
   réteg: azok a sáv KEZELÉSÉT másolnák, amire a mai sávnak megvan a saját,
   működő megoldása (húzás, egérgörgő, sínre kattintás).
3. **A sáv stílusa marad** 10 képpont széles és lapos. Ez **saját jogán**
   indokolt: a mai felületünk minden sávja ilyen (mappafa, párbeszédek,
   szerkesztő), és a 16 képpontos, három állapotképes rajz visszahozása az
   egész alkalmazás krómját szétszabdalná. ⚠️ A korábbi indoklás — „az eredeti
   csak natív Windows-króm volt" — **megdőlt** (#856): az eredeti saját,
   gondosan megrajzolt vezérlő volt. A stílusdöntés attól még áll, csak MÁS
   okból.

## Ami ebből következik a kódban

* `PicasaScrollBar.qml`: opcionális (`albumUgras`) gombpár + `elozoAlbum()` /
  `kovetkezoAlbum()` jelzés. **Alapból KI** — a többi sáv (mappafa,
  párbeszédek) változatlan marad; ott az album-ugrásnak nincs értelme.
* `LightboxFeed.qml`: `ugrasAlbumra(irany)` — a feed modellje maga a
  csoportlista, tehát az ugrás a szomszédos csoport elejére pozicionál.

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/app/qml/PicasaPy/PicasaScrollBar.qml`
- **Őrzi:** `tests/app/qml_functional/test_album_ugro_gombok_857.py`
