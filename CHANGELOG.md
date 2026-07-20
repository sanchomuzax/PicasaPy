# Változásnapló

A projekt a [Semantic Versioning](https://semver.org/) elvét követi; a `0.x`
sorozat instabil. A teljes, gépi generálású kiadási jegyzék a
[Releases](https://github.com/sanchomuzax/PicasaPy/releases) oldalon él — ez a
fájl a lényegi, ember által írt kiemeléseket rögzíti.

## [0.4.20] – 2026-07-20

### Javítva
- **crop64-lánc rossz kivágása (#130):** a `filters=` láncbeli `crop64` a spec
  szerint csak szerkesztési történet — a tényleges vágást a `crop=` kulcs
  (a lánc effektív, utolsó crop64-e) adja, az eredeti képméretre. A render
  eddig a lánc minden crop64-ét sorban, kaszkádolva alkalmazta → rossz
  kivágás a több crop64-es valódi Picasa-fájlokon. Mostantól az effektusok a
  teljes képre futnak, a vágás egyszer, a végén.
- **Legacy (nem UTF-8) `.picasa.ini` (#133):** a CP1250/latin-1 fájlok három
  hibája javítva — a U+0085/U+2028 kódpont nem töri ketté a sort
  (fantomszekció); ékezetes szöveg legacy fájlba mentése nem omlik el
  (UTF-8-ra váltás, végső esetben explicit `IniSaveError`); az IPTC 1:90
  karakterkészlet-jelölő figyelembevétele csökkenti a mojibake-et.
- **Döntés-csúszka kinullázta a mentett tilt-et (#131):** a döntés-eszköz a
  mentett értékről indul, és aktív eszköz melletti lapozás nem írja felül az
  új kép mentett döntését az előnézetben.
- **Feed-pozíció elveszett a nézőből visszatérve (#173):** a mappa végén álló
  kép megnyitása után visszalépve a feed a megnyitás előtti görgetési
  pozíción marad, nem ugrik a mappa elejére.

## [0.4.19] – 2026-07-20

### Javítva
- **Éles indexkép szerkesztett/vágott képnél (#163, P0):** a `filters=` lánc
  mostantól nagy (a célméret négyszeres) bázison renderel, és csak a
  végeredmény kicsinyül a bélyegkép-méretre — az erős vágás után sem homályos
  a rács legnagyobb fokozatán. A szerkesztett bélyegkép külön, a lánccal
  kulcsolt cache-fájlba kerül.
- **Óriáskép (DecompressionBomb) nem akasztja meg a szinkront (#134):** a
  metaadat-olvasó és a thumbnail-út elkapja a Pillow `DecompressionBombError`-t
  (és a szigorú `DecompressionBombWarning`-ot); egyetlen túl nagy kép többé nem
  dönti el a teljes indexelést.
- **Üres gyökér nem törli az indexet (#132):** ha egy figyelt gyökér elérhető,
  de üres (tipikusan lecsatolt NAS-mount), a szinkron nem takarítja ki a
  korábban felindexelt részfát — a NAS visszatérésekor nincs órákig tartó
  teljes újraépítés.
- **A fájlkezelő-megnyitás hibája eljut a felhasználóhoz (#112):** a „Keresés a
  lemezen" mostantól hibát jelez, ha az `xdg-open` hiányzik vagy nemnulla
  kóddal tér vissza — nem nyeli el némán.
