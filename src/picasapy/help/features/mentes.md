# Mentés, visszaállítás, visszavonás

A PicasaPy alapból nem nyúl a fájljaidhoz: a szerkesztéseket a képek
melletti `.picasa.ini` fájlban tartja. Ha viszont a **fájlba** is bele
akarod égetni a változtatásokat — mert máshol nyitod meg, vagy elküldöd
—, ezek a parancsok állnak rendelkezésre.

## Mentés

**Fájl ▸ Mentés** (Ctrl+S) a kijelölt képeket a szerkesztésekkel együtt
kiírja a lemezre.

A program **biztonsági másolatot készít** a fájlokról, és ezt a
megerősítő ablakban ki is írja. A másolat az eredeti mappában marad, egy
külön almappában, így később még visszaléphetsz.

Ez a megőrzött eredeti **együtt mozog a képpel**: ha átnevezed,
áthelyezed vagy lemásolod a fotót, a másolata is odakerül, és a
**Visszaállítás** az új helyen is működik. Ha a célhelyen valami útban
van, a művelet inkább el sem indul, és az üzenet megmondja, mi
akadályozza — a program soha nem ír felül egy másik kép megőrzött
eredetijét.

Ha valamelyik képen olyan szerkesztés van, amit a program még nem tud
megjeleníteni (például egy régi Picasa-változat effektje), a mentés előtt
figyelmeztet: „A mentés ezek nélkül írja ki a képet, és a beállítások
elvesznek. Ez nem vonható vissza."

Ha a mentés, a visszaállítás vagy a mentés visszavonása véget ér, a rács
és a megnyitott néző **magától frissül**: a nézőben a szerkesztő a lemezen
lévő friss fájlt és szerkesztéslistát olvassa újra, tehát azt látod, ami
most a fájlban van. Ha a művelet nem sikerül, **hibaablak** mondja meg az
okot.

## Mentés visszavonása

A mentés után megjelenő üzenetben a **Mentés visszavonása** gombbal
visszahozod a fájl mentés előtti állapotát — a szerkesztéseid közben
megmaradnak. Az üzenet ezt így mondja: „Az utolsó mentés visszavonásához
és a szerkesztések megtartásához kattintson a »Mentés visszavonása«
gombra." Csak a legutóbbi mentésre hat.

## Mentés másként és Másolat mentése

- **Fájl ▸ Mentés másként…** — a szerkesztett képet más néven, más helyre
  írja ki. JPEG és WebP formátumot kínál.
- **Fájl ▸ Másolat mentése** — az eredeti mellé ír egy szerkesztett
  másolatot, magától adott névvel.

Ha a választott név foglalt, a program szól: „A fájl mentése nem
lehetséges. Már van ilyen nevű fájl."

## Visszaállítás

**Fájl ▸ Visszaállítás** a fájlt az eredeti változatára állítja vissza.
Ez a mentéskor készült biztonsági másolatot használja, ezért csak akkor
kapcsolható be, ha van ilyen másolat.

A program rákérdez: „Visszaállítja ezeket a fájlokat az eredeti
változatra? Ez a művelet nem vonható vissza, és az összes módosítás
elvész."

## Összes szerkesztés visszavonása

**Kép ▸ Összes szerkesztés visszavonása** nem a fájlt, hanem a
szerkesztések listáját törli. A fájl érintetlen marad; a kép egyszerűen
újra úgy néz ki, mint eredetileg.

A program rákérdez, és külön figyelmeztet, ha a képen
**vörösszem-javítás** van: azt az **Újra** paranccsal sem lehet
visszahozni. A figyelmeztetés **megnevezi a képet** (több képnél
mindegyiket, vesszővel).

## Melyik mit csinál?

| parancs | mire hat | elvész-e a szerkesztés |
|---|---|---|
| Mentés | a fájlra a lemezen | nem, csak beleég |
| Mentés visszavonása | az utolsó lemezre írásra | nem |
| Visszaállítás | a fájlra a lemezen | igen |
| Összes szerkesztés visszavonása | csak a szerkesztéslistára | igen (a fájl ép) |

## Ha nem sikerül a mentés

- **„Fájlformázási hiba miatt a fájl nem menthető."** — a fájl formátumát
  a program nem tudja kiírni.
- **„A képet nem lehet kicserélni. Próbálja újra másik fájlnévvel."** — a
  cél fájl épp foglalt vagy nem írható.
- Ha a lemez megtelt vagy csak olvasható, a program erről is szól, és
  megnevezi az érintett fájlt.
